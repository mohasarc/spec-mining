#include <Python.h>
#include <structmember.h>
#include <socketmodule.h>  // Necessary for accessing the socket object's definitions

// Pointer to store the original settimeout function
static PyObject *(*original_settimeout)(PyObject *, PyObject *);

// Wrapper function to intercept calls to socket.settimeout
static PyObject *custom_settimeout(PyObject *self, PyObject *args) {
    printf("custom_settimeout called\n"); // Custom logging

    // Here, you can call additional Python code or handle arguments as necessary
    // For demonstration, let's log the timeout value if possible
    double timeout_value;
    if (!PyArg_ParseTuple(args, "d", &timeout_value)) {
        return NULL;  // Error parsing arguments
    }
    printf("Setting timeout to: %f seconds\n", timeout_value);

    // Call the original settimeout method
    return original_settimeout(self, args);
}

// Function to install the custom settimeout method
static PyObject *install_custom_settimeout(PyObject *module) {
    PyObject *socket_module = PyImport_ImportModule("socket");
    if (socket_module == NULL) {
        return NULL;
    }

    PyObject *socket_type = PyObject_GetAttrString(socket_module, "socket");
    if (socket_type == NULL) {
        Py_DECREF(socket_module);
        return NULL;
    }

    // Install the custom function
    original_settimeout = (PyObject *(*)(PyObject *, PyObject *))(((PyTypeObject *)socket_type)->tp_methods->tp_setattro);
    ((PyTypeObject *)socket_type)->tp_methods->tp_setattro = (setattrofunc)custom_settimeout;

    Py_DECREF(socket_type);
    Py_DECREF(socket_module);
    Py_RETURN_NONE;
}

// Function to restore the original settimeout method
static PyObject *uninstall_custom_settimeout(PyObject *module) {
    PyObject *socket_module = PyImport_ImportModule("socket");
    if (socket_module == NULL) {
        return NULL;
    }

    PyObject *socket_type = PyObject_GetAttrString(socket_module, "socket");
    if (socket_type == NULL) {
        Py_DECREF(socket_module);
        return NULL;
    }

    // Restore the original function
    ((PyTypeObject *)socket_type)->tp_methods->tp_setattro = (setattrofunc)original_settimeout;

    Py_DECREF(socket_type);
    Py_DECREF(socket_module);
    Py_RETURN_NONE;
}

// Module method definitions
static PyMethodDef module_methods[] = {
    {"install_custom_settimeout", install_custom_settimeout, METH_NOARGS, "Patches the socket settimeout method."},
    {"uninstall_custom_settimeout", uninstall_custom_settimeout, METH_NOARGS, "Restores the original socket settimeout method."},
    {NULL, NULL, 0, NULL}
};

// Module definition
static struct PyModuleDef customsettimeoutmodule = {
    PyModuleDef_HEAD_INIT,
    "customsettimeout",
    "Module to override and restore socket settimeout method.",
    -1,
    module_methods
};

// Initialize the module
PyMODINIT_FUNC PyInit_customsettimeout(void) {
    return PyModule_Create(&customsettimeoutmodule);
}
