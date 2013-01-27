#include <Python.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <libhdhomerun/hdhomerun.h>

#define PORT_OFFSET 3300

#define TS_PACKET_SIZE 188
#define RX_BUFFER_SIZE 21*TS_PACKET_SIZE

#define MAX_NUMBER_OF_TUNERS 4
#define RECORDINGS_PER_TUNER 4

#define FALSE 0
#define TRUE 1

#define MESSAGE_THRESHOLD 0

#define UPD_RX_BUFFER 8388608

/* TYPES */

typedef struct prgcfg_t{
  uint16_t ch;
  uint16_t pid;
  uint16_t vid;
  uint16_t aid;
  uint16_t sid;
}prgcfg_t;

struct index_bf{
  uint8_t tun;
  uint8_t rec;
};

typedef union handle_t{
  struct index_bf idx;
  int16_t id;
}handle_t;

typedef struct recording_t{
  prgcfg_t cfg;
  FILE *fd;
}recording_t;

typedef struct tuner_t{
  int16_t ch;
  uint8_t index;
  int socket;
  int16_t port;
  int32_t device_id;
  int8_t active;
  recording_t recording[RECORDINGS_PER_TUNER];
}tuner_t;

/* MODULE VARS */

tuner_t *tuner[MAX_NUMBER_OF_TUNERS];
uint8_t installed_tuners = 0;
static PyObject *my_callback = NULL;
char target_ip[16] = "10.0.0.3";

/* PROTOTYPES */

int16_t get_available_recorder_handle(prgcfg_t *cfg);
void handlePacket(handle_t *h, uint8_t *data);
recording_t *get_recording(handle_t *h);
tuner_t *get_tuner(handle_t *h);

/* IMPLEMENTATION */

static PyObject *
hdhr_set_recorder_ip(PyObject *self, PyObject *args)
{
  static char* temp;
  
  if (!PyArg_ParseTuple(args, "s", &temp))
  {
    return NULL;
  }
  strcpy(target_ip, temp);
//  printf("%s\n", target_ip);
  
  Py_RETURN_NONE;
    
}

static PyObject *
hdhr_install_tuner(PyObject *self, PyObject *args)
{
  int32_t id;
  int32_t index;
  int32_t rx_size;
  socklen_t optlen;

  struct sockaddr_in serveraddr;
  tuner_t *new_tuner;

  if (!PyArg_ParseTuple(args, "ll", &id, &index)) // should be "ki", but does not work
  {
    return NULL;
  }
//  printf("%lX\n", id);
  new_tuner = (tuner_t*) malloc(sizeof(tuner_t));
  memset(new_tuner, 0, sizeof(tuner_t));
  
  new_tuner->device_id = id;
  new_tuner->index = index;
  new_tuner->port = PORT_OFFSET + installed_tuners;

  /* get a socket descriptor */
  if((new_tuner->socket = socket(AF_INET, SOCK_DGRAM, 0)) < 0)
  {
    perror("UDP server - socket() error");
    exit(-1);
  }

  rx_size = UPD_RX_BUFFER;
  setsockopt(new_tuner->socket, SOL_SOCKET, SO_RCVBUF, (char *)&rx_size, sizeof(int32_t));
  
  rx_size = 0;
  optlen = sizeof(int32_t);
  getsockopt(new_tuner->socket, SOL_SOCKET, SO_RCVBUF, (char *)&rx_size, &optlen);
  printf("rx: %ld\n", rx_size);

  /* bind to address */
  memset(&serveraddr, 0x00, sizeof(serveraddr));
  serveraddr.sin_family = AF_INET;
  serveraddr.sin_port = htons(new_tuner->port);
  serveraddr.sin_addr.s_addr = htonl(INADDR_ANY);
  
  if(bind(new_tuner->socket, (struct sockaddr *)&serveraddr, sizeof(serveraddr)) < 0)
  {
    perror("UDP server - bind() error");
    close(new_tuner->socket);
    exit(-1);
  }
  
  tuner[installed_tuners++] = new_tuner;
  
  Py_RETURN_NONE;
    
}

static PyObject *
hdhr_record(PyObject *self, PyObject *args)
{
  static char *filename;
  prgcfg_t cfg;
  handle_t h;
  
  if (!PyArg_ParseTuple(args, "HHHHHs", &cfg.ch, &cfg.vid, &cfg.aid, &cfg.sid, &cfg.pid, &filename))
  {
    return NULL;
  }
  
  h.id = get_available_recorder_handle(&cfg);
  get_recording(&h)->fd = fopen(filename, "wb");
  get_tuner(&h)->active++;
//  printf("act: %d\n", get_tuner(&h)->active);
  return Py_BuildValue("h", h.id);
}

static PyObject *
hdhr_stop(PyObject *self, PyObject *args)
{
  handle_t h;
  tuner_t *tun;
  struct hdhomerun_device_t *hdhr_device;

  if (!PyArg_ParseTuple(args, "h", &h.id))
  {
    return NULL;
  }

  if ((h.id >= 0) && (get_recording(&h)->fd != NULL))
  {
    fclose(get_recording(&h)->fd);
    memset(get_recording(&h), 0, sizeof(recording_t));
    get_recording(&h)->fd = NULL;
    tun = get_tuner(&h);
    tun->active--;
    if(tun->active < 1)
    {
      printf("Stopping tuner%d\n", h.idx.tun);
      hdhr_device = hdhomerun_device_create(tun->device_id, 0, tun->index, NULL);
      hdhomerun_device_set_tuner_channel(hdhr_device, "none");
      hdhomerun_device_set_tuner_target(hdhr_device, "none");
      hdhomerun_device_destroy(hdhr_device);
      
      tun->active = 0;
      tun->ch = 0;
    }    
  }
  
  Py_RETURN_NONE;
}

static PyObject *
hdhr_run(PyObject *self, PyObject *args)
{
  int rc, sc;
  uint8_t buffer[RX_BUFFER_SIZE];
  uint8_t *bufptr = buffer;
  int buflen = sizeof(buffer);
  int i=0;
  struct timeval timeout;
  fd_set fds;
  uint8_t ti = 0;
  handle_t h;
  static int32_t next_callback_time = 0;
  int skew = 0;
  
  PyObject_CallObject(my_callback, NULL);
  next_callback_time = time(NULL) + 10;
  
  while(1){
    timeout.tv_sec = 10;
    timeout.tv_usec = 0;
    
    FD_ZERO(&fds);
    
    for (ti = 0; ti < installed_tuners; ti++)
    {
      FD_SET(tuner[ti]->socket, &fds);
    }

    rc = select(sizeof(fds)*8, &fds, NULL, NULL, &timeout);
    
    if(rc < 0)
    {
      perror("select failed");
      exit(-1);
    }
    else if (rc > 0)
    {
      h.id = 0;
      for (h.idx.tun = 0; h.idx.tun < installed_tuners; h.idx.tun++)
      {
        sc = get_tuner(&h)->socket;
        if (FD_ISSET(sc, &fds))
        {
          rc = recvfrom(sc, bufptr, buflen, 0, NULL, NULL);
          skew = rc % TS_PACKET_SIZE;
          if (skew)
          {
            printf("num: %d skew: %d\n", rc / TS_PACKET_SIZE, skew);          
          }
          i = -1;
          do
          {
            while((bufptr[++i] != 0x47) && (i < 2 * TS_PACKET_SIZE))
            {
              printf (".");
            }
          }
          while(((bufptr[i + TS_PACKET_SIZE] != 0x47) || (bufptr[i + 2 * TS_PACKET_SIZE] != 0x47)) && (i < 2 * TS_PACKET_SIZE));
 
          while (i <= (rc - TS_PACKET_SIZE))
          {
            handlePacket(&h, bufptr+i);
            i += TS_PACKET_SIZE;
          }    
        }
      }
    }
    if (next_callback_time <= time(NULL))
    {
      PyObject_CallObject(my_callback, NULL);
      next_callback_time = time(NULL) + 10;
    }
  }
  Py_RETURN_NONE;
}

void handlePacket(handle_t *h, uint8_t *data)
{
  int pid;
  int tei, scrambled, af_reserved;
  handle_t lh;
  prgcfg_t *cfg;
  recording_t *rec;
  
  lh.id = h->id;
 
  if (data[0] == 0x47)
  {
    pid = ((data[1] & 0x1f) << 8) + data[2];
    
    tei = ((data[1] & 0x80) != 0);
    scrambled = ((data[3] & 0xc0) != 0);
    af_reserved = ((data[3] & 0x30) == 0);
    if (tei || scrambled || af_reserved)
    {
      return;
    }
    //printf("%d\n", pid);
    for (lh.idx.rec=0; lh.idx.rec < RECORDINGS_PER_TUNER; lh.idx.rec++)
    {
      rec = get_recording(&lh);
      cfg = &rec->cfg;
      if ((pid == cfg->vid) || (pid == cfg->aid) || (pid == cfg->sid || (pid == cfg->pid) || (pid == 0)))
      {
        if (rec->fd != NULL)
        {
          fwrite(data, TS_PACKET_SIZE, 1, rec->fd);
        }
      }
    }
  }else{
    printf("m");
  }
}

int16_t get_available_recorder_handle(prgcfg_t *cfg)
{
  handle_t h;
  tuner_t *tun;
  char string[24];
  struct hdhomerun_device_t *hdhr_device;
  
  h.id = 0;
  
  for (h.idx.tun = 0; h.idx.tun < installed_tuners; h.idx.tun++)
  {
    if (tuner[h.idx.tun]->ch == cfg->ch)
    {
      for (h.idx.rec = 0; h.idx.rec < RECORDINGS_PER_TUNER; h.idx.rec++)
      {
        if (get_recording(&h)->cfg.pid == 0)
        {
          printf("Using free recording slot on tuner%d\n", h.idx.tun);
          memcpy(&get_recording(&h)->cfg, cfg, sizeof(prgcfg_t));
          return h.id;
        }
      }
    }
  }
  
  h.id = 0;
  
  for (h.idx.tun = 0; h.idx.tun < installed_tuners; h.idx.tun++)
  {
    tun = get_tuner(&h);
    if (tun->ch == 0)
    {
      printf("Starting tuner%d\n", h.idx.tun);
      memcpy(&get_recording(&h)->cfg, cfg, sizeof(prgcfg_t));
      tun->ch = cfg->ch;
      hdhr_device = hdhomerun_device_create(tun->device_id, 0, tun->index, NULL);
      sprintf(string, "%d", tun->ch);
//      printf("%x\n", hdhomerun_device_get_device_ip(hdhr_device));
      hdhomerun_device_set_tuner_channel(hdhr_device, string);
      hdhomerun_device_set_tuner_filter(hdhr_device, "none");
      hdhomerun_device_set_tuner_program(hdhr_device, "0");
      sprintf(string, "%s:%d", target_ip, tun->port);
//      printf("%s\n", string);
      hdhomerun_device_set_tuner_target(hdhr_device, string);
      hdhomerun_device_destroy(hdhr_device);
      return h.id;
    }
  }
  
  return -1;
}

recording_t *get_recording(handle_t *h)
{
  return &tuner[h->idx.tun]->recording[h->idx.rec];
}

tuner_t *get_tuner(handle_t *h)
{
  return tuner[h->idx.tun];
}

static PyObject *
hdhr_set_callback(PyObject *dummy, PyObject *args)
{
    PyObject *temp;

    if (PyArg_ParseTuple(args, "O:set_callback", &temp)) {
        if (!PyCallable_Check(temp)) {
            PyErr_SetString(PyExc_TypeError, "parameter must be callable");
            return NULL;
        }
        Py_XINCREF(temp);         /* Add a reference to new callback */
        Py_XDECREF(my_callback);  /* Dispose of previous callback */
        my_callback = temp;       /* Remember new callback */
        
        Py_RETURN_NONE;
    }
    return NULL;
}



void message(char *message, int level)
{
  if (level >= MESSAGE_THRESHOLD)
  {
    printf(message);
  }
}

/* PYTHON STUFF */

static PyMethodDef hdhr_methods[] =
{
  {"set_recorder_ip", hdhr_set_recorder_ip, METH_VARARGS, "Test"},
  {"install_tuner", hdhr_install_tuner, METH_VARARGS, "Test"},
  {"set_callback", hdhr_set_callback, METH_VARARGS, "Test"},
  {"record", hdhr_record, METH_VARARGS, "Test"},
  {"stop", hdhr_stop, METH_VARARGS, "Test"},
  {"run", hdhr_run, METH_VARARGS, "Test"},
  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
inithdhr(void)
{
  (void) Py_InitModule("hdhr", hdhr_methods);
}
