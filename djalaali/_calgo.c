/*
 * C implementation of the Jalaali conversion algorithm in djalaali/algo.py.
 *
 * Ported from https://github.com/jalaali/go-jalaali
 *
 * Built against the stable ABI (abi3), so a single wheel per platform serves
 * every supported Python version. C integer division and remainder truncate
 * toward zero, exactly like Go's, so the formulas are copied verbatim.
 *
 * Arguments that do not fit comfortably in 64-bit arithmetic are handed to
 * the pure-Python implementation registered through setup(), which keeps
 * the behaviour (including exceptions) identical for every input.
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>

#define N_BREAKS 20
#define MAX_ARG 1000000000000LL /* keeps every intermediate within int64 */

static const int64_t BREAKS[N_BREAKS] = {
    -61,  9,    38,   199,  426,  686,  756,  818,  1111, 1181,
    1210, 1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178,
};

static PyObject *error_type = NULL;
static PyObject *py_to_jalaali = NULL;
static PyObject *py_to_gregorian = NULL;
static PyObject *py_is_leap_year = NULL;
static PyObject *py_month_length = NULL;

/* Returns 0 on success, -1 with an exception set, 1 if too large for C. */
static int
get_arg(PyObject *obj, int64_t *out)
{
    int overflow = 0;
    long long v = PyLong_AsLongLongAndOverflow(obj, &overflow);
    if (v == -1 && PyErr_Occurred()) {
        return -1;
    }
    if (overflow || v > MAX_ARG || v < -MAX_ARG) {
        return 1;
    }
    *out = v;
    return 0;
}

static int
get_args(PyObject *args, int n, int64_t *out)
{
    if (PyTuple_Size(args) != n) {
        PyErr_Format(PyExc_TypeError, "expected %d arguments, got %zd", n,
                     PyTuple_Size(args));
        return -1;
    }
    int too_big = 0;
    for (int i = 0; i < n; i++) {
        int r = get_arg(PyTuple_GetItem(args, i), &out[i]);
        if (r < 0) {
            return -1;
        }
        too_big |= r;
    }
    return too_big;
}

static void
raise_invalid_year(int64_t year)
{
    PyObject *exc = PyObject_CallFunction(error_type, "L", (long long)year);
    if (exc != NULL) {
        PyErr_SetObject(error_type, exc);
        Py_DECREF(exc);
    }
}

/* Returns 0 on success, -1 (without an exception set) for an invalid year. */
static int
jal_cal(int64_t jy, int64_t *leap, int64_t *gy, int64_t *march)
{
    int64_t g = jy + 621;
    int64_t leap_j = -14;
    int64_t jp = BREAKS[0];
    int64_t jump = 0;

    if (jy < jp || jy >= BREAKS[N_BREAKS - 1]) {
        return -1;
    }

    for (int i = 1; i < N_BREAKS; i++) {
        int64_t jm = BREAKS[i];
        jump = jm - jp;
        if (jy < jm) {
            break;
        }
        leap_j += (jump / 33) * 8 + (jump % 33) / 4;
        jp = jm;
    }

    int64_t n = jy - jp;
    leap_j += (n / 33) * 8 + (n % 33 + 3) / 4;
    if (jump % 33 == 4 && jump - n == 4) {
        leap_j += 1;
    }

    int64_t leap_g = g / 4 - ((g / 100 + 1) * 3) / 4 - 150;

    if (jump - n < 6) {
        n = n - jump + ((jump + 4) / 33) * 33;
    }

    int64_t l = ((n + 1) % 33 - 1) % 4;
    if (l == -1) {
        l = 4;
    }

    *leap = l;
    *gy = g;
    *march = 20 + leap_j - leap_g;
    return 0;
}

static int64_t
g2d(int64_t gy, int64_t gm, int64_t gd)
{
    int64_t d = ((gy + (gm - 8) / 6 + 100100) * 1461) / 4 +
                (153 * ((gm + 9) % 12) + 2) / 5 + gd - 34840408;
    d = d - (((gy + 100100 + (gm - 8) / 6) / 100) * 3) / 4 + 752;
    return d;
}

static void
d2g(int64_t jdn, int64_t *gy, int64_t *gm, int64_t *gd)
{
    int64_t j = 4 * jdn + 139361631;
    j = j + (((4 * jdn + 183187720) / 146097) * 3) / 4 * 4 - 3908;
    int64_t i = ((j % 1461) / 4) * 5 + 308;
    *gd = (i % 153) / 5 + 1;
    *gm = (i / 153) % 12 + 1;
    *gy = j / 1461 - 100100 + (8 - *gm) / 6;
}

static int64_t
month_len(int64_t jy, int64_t jm, int *err)
{
    *err = 0;
    if (jm <= 6) {
        return 31;
    }
    if (jm <= 11) {
        return 30;
    }
    int64_t leap, gy, march;
    if (jal_cal(jy, &leap, &gy, &march) < 0) {
        *err = 1;
        return 0;
    }
    return leap == 0 ? 30 : 29;
}

static PyObject *
fallback(PyObject *func, PyObject *args)
{
    return PyObject_CallObject(func, args);
}

static PyObject *
calgo_to_jalaali(PyObject *self, PyObject *args)
{
    int64_t a[3];
    int r = get_args(args, 3, a);
    if (r < 0) {
        return NULL;
    }
    if (r > 0) {
        return fallback(py_to_jalaali, args);
    }

    int64_t gy, gm, gd;
    int64_t jdn = g2d(a[0], a[1], a[2]);
    d2g(jdn, &gy, &gm, &gd);

    int64_t jy = gy - 621;
    int64_t leap, g, march;
    if (jal_cal(jy, &leap, &g, &march) < 0) {
        raise_invalid_year(jy);
        return NULL;
    }
    int64_t k = jdn - g2d(gy, 3, march);
    int64_t jm, jd;
    if (k >= 0) {
        if (k <= 185) {
            return Py_BuildValue("(LLL)", (long long)jy,
                                 (long long)(1 + k / 31),
                                 (long long)(k % 31 + 1));
        }
        k -= 186;
    }
    else {
        jy -= 1;
        k += 179;
        if (leap == 1) {
            k += 1;
        }
    }
    jm = 7 + k / 30;
    jd = k % 30 + 1;
    return Py_BuildValue("(LLL)", (long long)jy, (long long)jm,
                         (long long)jd);
}

static PyObject *
calgo_to_gregorian(PyObject *self, PyObject *args)
{
    int64_t a[3];
    int r = get_args(args, 3, a);
    if (r < 0) {
        return NULL;
    }
    if (r > 0) {
        return fallback(py_to_gregorian, args);
    }
    int64_t jy = a[0], jm = a[1], jd = a[2];

    int valid = !(jy < -61 || jy > 3177 || jm < 1 || jm > 12 || jd < 1);
    if (valid) {
        int err;
        valid = jd <= month_len(jy, jm, &err);
    }
    if (!valid) {
        return PyErr_Format(
            PyExc_ValueError,
            "invalid jalaali date: year=%lld, month=%lld, day=%lld",
            (long long)jy, (long long)jm, (long long)jd);
    }

    int64_t leap, gy, march;
    if (jal_cal(jy, &leap, &gy, &march) < 0) {
        raise_invalid_year(jy);
        return NULL;
    }
    int64_t jm7 = jm / 7;
    int64_t jdn = g2d(gy, 3, march) + (jm - 1) * 31 - jm7 * (jm - 7) + jd - 1;
    int64_t y, m, d;
    d2g(jdn, &y, &m, &d);
    return Py_BuildValue("(LLL)", (long long)y, (long long)m, (long long)d);
}

static PyObject *
calgo_is_leap_year(PyObject *self, PyObject *args)
{
    int64_t a[1];
    int r = get_args(args, 1, a);
    if (r < 0) {
        return NULL;
    }
    if (r > 0) {
        return fallback(py_is_leap_year, args);
    }
    int64_t leap, gy, march;
    if (jal_cal(a[0], &leap, &gy, &march) < 0) {
        raise_invalid_year(a[0]);
        return NULL;
    }
    return PyBool_FromLong(leap == 0);
}

static PyObject *
calgo_month_length(PyObject *self, PyObject *args)
{
    int64_t a[2];
    int r = get_args(args, 2, a);
    if (r < 0) {
        return NULL;
    }
    if (r > 0) {
        return fallback(py_month_length, args);
    }
    int err;
    int64_t n = month_len(a[0], a[1], &err);
    if (err) {
        raise_invalid_year(a[0]);
        return NULL;
    }
    return PyLong_FromLongLong(n);
}

static PyObject *
calgo_setup(PyObject *self, PyObject *args)
{
    PyObject *e, *a, *b, *c, *d;
    if (!PyArg_ParseTuple(args, "OOOOO", &e, &a, &b, &c, &d)) {
        return NULL;
    }
    Py_INCREF(e);
    Py_XDECREF(error_type);
    error_type = e;
    Py_INCREF(a);
    Py_XDECREF(py_to_jalaali);
    py_to_jalaali = a;
    Py_INCREF(b);
    Py_XDECREF(py_to_gregorian);
    py_to_gregorian = b;
    Py_INCREF(c);
    Py_XDECREF(py_is_leap_year);
    py_is_leap_year = c;
    Py_INCREF(d);
    Py_XDECREF(py_month_length);
    py_month_length = d;
    Py_RETURN_NONE;
}

static PyMethodDef methods[] = {
    {"to_jalaali", calgo_to_jalaali, METH_VARARGS,
     "to_jalaali(gy, gm, gd) -> (jy, jm, jd)"},
    {"to_gregorian", calgo_to_gregorian, METH_VARARGS,
     "to_gregorian(jy, jm, jd) -> (gy, gm, gd)"},
    {"is_leap_year", calgo_is_leap_year, METH_VARARGS,
     "is_leap_year(jy) -> bool"},
    {"month_length", calgo_month_length, METH_VARARGS,
     "month_length(jy, jm) -> int"},
    {"setup", calgo_setup, METH_VARARGS,
     "setup(error_type, to_jalaali, to_gregorian, is_leap_year, "
     "month_length): register the exception class and Python fallbacks"},
    {NULL, NULL, 0, NULL},
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "djalaali._calgo", NULL, -1, methods,
};

PyMODINIT_FUNC
PyInit__calgo(void)
{
    return PyModule_Create(&module);
}
