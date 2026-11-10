from setuptools import Extension, setup

# Optional C accelerator for djalaali.algo, built against the stable ABI so a
# single wheel per platform covers every supported Python. If compilation
# fails (no compiler, unsupported platform) the install still succeeds and
# the pure-Python implementation is used.
setup(
    ext_modules=[
        Extension(
            "djalaali._calgo",
            sources=["djalaali/_calgo.c"],
            define_macros=[("Py_LIMITED_API", "0x03090000")],
            py_limited_api=True,
            optional=True,
        )
    ],
    options={"bdist_wheel": {"py_limited_api": "cp39"}},
)
