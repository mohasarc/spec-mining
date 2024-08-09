#include <Python.h>

static PyObject *original_create_connection = NULL;

// Define the custom create_connection function
static PyObject *custom_create_connection(PyObject *self, PyObject *args, PyObject *kwds) {
    printf("custom_create_connection called\n");

    // Optionally, add any pre-call modification or logging here

    // Call the original create_connection with the passed arguments and keyword arguments
    PyObject *result = PyObject_Call(original_create_connection, args, kwds);
    if (!result) {
        PyErr_Print();
        return NULL; // Properly handle and forward errors
    }

    // Optionally, add any post-call processing here

    return result;
}

// Function to install the custom create_connection
static PyObject *install_custom_create_connection(PyObject *module) {
    PyObject *socket_module = PyImport_ImportModule("socket");
    if (!socket_module) {
        PyErr_SetString(PyExc_ImportError, "Failed to import socket module.");
        return NULL;
    }

    // Retrieve the original create_connection
    original_create_connection = PyObject_GetAttrString(socket_module, "create_connection");
    if (!original_create_connection) {
        PyErr_SetString(PyExc_AttributeError, "Failed to retrieve socket.create_connection.");
        Py_DECREF(socket_module);
        return NULL;
    }

    // Increase reference to keep around
    Py_INCREF(original_create_connection);

    // Create a new function object for our custom function
    static PyMethodDef method_def = {
        "create_connection",
        (PyCFunction)custom_create_connection,
        METH_VARARGS | METH_KEYWORDS,
        "Custom socket create_connection function"
    };
    PyObject *custom_function = PyCFunction_New(&method_def, NULL);
    if (!custom_function) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create custom function.");
        Py_DECREF(socket_module);
        return NULL;
    }

    // Replace the create_connection in the socket module with our custom function
    if (PyObject_SetAttrString(socket_module, "create_connection", custom_function) != 0) {
        PyErr_Print();
        Py_DECREF(custom_function);
        Py_DECREF(socket_module);
        return NULL;
    }

    Py_DECREF(custom_function);  // The module now holds a reference
    Py_DECREF(socket_module);    // Clean up our reference to the socket module
    Py_RETURN_NONE;
}

static PyMethodDef CustomMethods[] = {
    {"install_custom_create_connection", install_custom_create_connection, METH_NOARGS, "Install custom create_connection function."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef customsocketmodule = {
    PyModuleDef_HEAD_INIT,
    "customsocket",
    "Module to override the socket.create_connection function.",
    -1,
    CustomMethods
};

PyMODINIT_FUNC PyInit_customsocket(void) {
    return PyModule_Create(&customsocketmodule);
}
