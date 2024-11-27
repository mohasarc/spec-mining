#include <Python.h>
#include <structmember.h>
#include <sys/socket.h>
#include <netinet/in.h>

static PyObject* Socket_send_event(PyObject* self, PyObject* args) {
    printf("Socket object reference: %p\n", self);
    Py_RETURN_NONE;
}

static PyMethodDef Socket_methods[] = {
    {"send_event", (PyCFunction) Socket_send_event, METH_NOARGS, "Prints the self reference"},
    {NULL, NULL, 0, NULL}  /* Sentinel */
};

static struct PyModuleDef socketextensionmodule = {
    PyModuleDef_HEAD_INIT,
    "socketextension",
    "Extension module that adds a send_event method to socket.socket",
    -1,
    Socket_methods
};

PyMODINIT_FUNC PyInit_socketextension(void) {
    PyObject* module;
    PyObject* socket_module;
    PyObject* socket_class;

    module = PyModule_Create(&socketextensionmodule);
    if (module == NULL) {
        return NULL;
    }

    socket_module = PyImport_ImportModule("socket");
    if (socket_module == NULL) {
        return NULL;
    }

    socket_class = PyObject_GetAttrString(socket_module, "socket");
    if (socket_class == NULL) {
        return NULL;
    }

    if (PyType_Check(socket_class)) {
        if (PyType_Ready((PyTypeObject *)socket_class) < 0) {
            return NULL;
        }
        if (PyModule_AddFunctions(socket_class, Socket_methods) < 0) {
            return NULL;
        }
    }

    Py_DECREF(socket_module);
    Py_DECREF(socket_class);

    return module;
}
