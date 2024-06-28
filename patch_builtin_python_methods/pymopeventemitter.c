#include <Python.h>
#include <structmember.h>
#include <stdlib.h>

typedef struct {
    PyObject_HEAD
    PyObject *events; // Dictionary storing events and their listeners.
} PyMopEventEmitter;


__attribute__((visibility("default")))
PyMopEventEmitter *global_event_emitter = NULL;

static void
PyMopEventEmitter_dealloc(PyMopEventEmitter* self)
{
    Py_XDECREF(self->events);
    Py_TYPE(self)->tp_free((PyObject*) self);
}

__attribute__((visibility("default")))
PyObject *
PyMopEventEmitter_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyMopEventEmitter *self;
    self = (PyMopEventEmitter *)type->tp_alloc(type, 0);

    // Assuming Python's GIL is already held or your context ensures it
    PyObject *pName = PyUnicode_FromString("my_python_functions");
    PyObject *pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (pModule != NULL) {
        PyObject *pFunc = PyObject_GetAttrString(pModule, "my_custom_function");

        if (pFunc && PyCallable_Check(pFunc)) {
            PyObject *pValue = PyObject_CallObject(pFunc, NULL);  // Call without arguments

            if (pValue != NULL) {
                Py_DECREF(pValue);
            } else {
                PyErr_Print();  // Handle error appropriately
            }
        } else {
            PyErr_Print();
        }

        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
    } else {
        PyErr_Print();
    }


    if (self != NULL) {
        self->events = PyDict_New();
        if (self->events == NULL) {
            Py_DECREF(self);
            return NULL;
        }
    }
    return (PyObject *)self;
}

static int
PyMopEventEmitter_init(PyMopEventEmitter *self, PyObject *args, PyObject *kwds)
{
    return 0;
}

static PyObject *
PyMopEventEmitter_subscribe(PyMopEventEmitter* self, PyObject *args)
{
    PyObject *event_name;
    PyObject *callback;

    if (!PyArg_ParseTuple(args, "OO", &event_name, &callback)) {
        return NULL;
    }

    if (!PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "parameter must be callable");
        return NULL;
    }

    PyObject *listeners = PyDict_GetItem(self->events, event_name);
    if (listeners == NULL) {
        listeners = PyList_New(0);
        PyDict_SetItem(self->events, event_name, listeners);
        Py_DECREF(listeners);
    }

    PyList_Append(listeners, callback);
    Py_INCREF(callback);
    Py_RETURN_NONE;
}

static PyObject *
PyMopEventEmitter_emit(PyMopEventEmitter* self, PyObject *args)
{
    PyObject *event_name;
    if (!PyArg_ParseTuple(args, "O", &event_name)) {
        return NULL;
    }

    PyObject *listeners = PyDict_GetItem(self->events, event_name);
    if (listeners != NULL) {
        Py_ssize_t count = PyList_Size(listeners);
        for (Py_ssize_t i = 0; i < count; i++) {
            PyObject *callback = PyList_GetItem(listeners, i);
            if (callback != NULL) {
                PyObject_CallObject(callback, NULL);
            }
        }
    }
    Py_RETURN_NONE;
}

static PyTypeObject PyMopEventEmitterType;

static PyObject *
PyMopEventEmitter_get_global_emitter(PyMopEventEmitter* self, PyObject *args)
{
    Py_INCREF(global_event_emitter);
    return (PyObject *)global_event_emitter;
}

static PyMethodDef PyMopEventEmitter_methods[] = {
    {"subscribe", (PyCFunction) PyMopEventEmitter_subscribe, METH_VARARGS,
     "Subscribe to an event with a callback."},
    {"emit", (PyCFunction) PyMopEventEmitter_emit, METH_VARARGS,
     "Emit an event, calling all subscribed callbacks."},
    {"get_global_emitter", (PyCFunction) PyMopEventEmitter_get_global_emitter,
    METH_NOARGS, "Get the global event emitter instance."},
    {NULL}  /* Sentinel */
};

static PyTypeObject PyMopEventEmitterType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "pymopeventemitter.PyMopEventEmitter",
    .tp_doc = "Event Emitter",
    .tp_basicsize = sizeof(PyMopEventEmitter),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = PyMopEventEmitter_new,
    .tp_init = (initproc) PyMopEventEmitter_init,
    .tp_dealloc = (destructor) PyMopEventEmitter_dealloc,
    .tp_methods = PyMopEventEmitter_methods,
};

static PyModuleDef pymopeventemittermodule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "pymopeventemitter",
    .m_doc = "Example module that creates an event emitter.",
    .m_size = -1,
};

PyMODINIT_FUNC
PyInit_pymopeventemitter(void)
{
    if (PyType_Ready(&PyMopEventEmitterType) < 0)
        return NULL;

    PyObject *m = PyModule_Create(&pymopeventemittermodule);
    if (m == NULL)
        return NULL;

    global_event_emitter = (PyMopEventEmitter *)PyMopEventEmitter_new(&PyMopEventEmitterType, NULL, NULL);
    if (global_event_emitter == NULL)
        return NULL;

    Py_INCREF(global_event_emitter);  // Increment the reference count

    Py_INCREF(&PyMopEventEmitterType);
    if (PyModule_AddObject(m, "PyMopEventEmitter", (PyObject *)&PyMopEventEmitterType) < 0) {
        Py_DECREF(&PyMopEventEmitterType);
        Py_DECREF(m);
        return NULL;
    }

    return m;
}
