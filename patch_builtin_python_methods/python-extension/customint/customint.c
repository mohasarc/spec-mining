#include <Python.h>

// Original bit_length function pointer
static PyObject *(*original_bit_length)(PyObject *);

// New bit_length method
static PyObject *custom_bit_length(PyObject *self) {
    // Assuming Python's GIL is already held or your context ensures it

    // Call the original bit_length method to get the result
    PyObject *result = original_bit_length(self);
    if (!result) return NULL; // If there's an error, return immediately

    // find the module and function and call it
    PyObject *pName = PyUnicode_FromString("pythonmop.instrumentation");
    PyObject *pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (pModule != NULL) {
        PyObject *pFunc = PyObject_GetAttrString(pModule, "log_int_value");

        if (pFunc && PyCallable_Check(pFunc)) {
            // Create a tuple containing the integer object, its value, and the bit_length result
            PyObject *args = PyTuple_New(3);
            Py_INCREF(self); // Increment ref count of self since PyTuple_SetItem steals a reference
            PyTuple_SetItem(args, 0, self);

            PyObject *value = PyObject_Str(self);
            PyTuple_SetItem(args, 1, value); // Tuple steals the reference to value

            Py_INCREF(result); // Increment ref count of result to pass it safely
            PyTuple_SetItem(args, 2, result);

            PyObject *pValue = PyObject_CallObject(pFunc, args);  // Call with the tuple as argument
            Py_DECREF(args);  // Decrement reference count of args tuple

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

    return result;
}

// Function to replace the bit_length method of the int type
static PyObject *install_custom_bit_length(PyObject *module) {
    // Find the 'bit_length' method in the list of methods for the int type
    PyMethodDef *methods = PyLong_Type.tp_methods;
    for (; methods->ml_name != NULL; methods++) {
        if (strcmp(methods->ml_name, "bit_length") == 0) {
            original_bit_length = (PyObject *(*)(PyObject *))methods->ml_meth;
            methods->ml_meth = (PyCFunction)custom_bit_length;
            break;
        }
    }
    Py_RETURN_NONE;
}

// Module method definitions
static PyMethodDef module_methods[] = {
    {"install_custom_bit_length", install_custom_bit_length, METH_NOARGS, "Patches the int bit_length method."},
    {NULL, NULL, 0, NULL}
};

// Module definition
static struct PyModuleDef customintmodule = {
    PyModuleDef_HEAD_INIT,
    "customint",
    "Module to override int bit_length method.",
    -1,
    module_methods
};

// Initialize the module
PyMODINIT_FUNC PyInit_customint(void) {
    return PyModule_Create(&customintmodule);
}
