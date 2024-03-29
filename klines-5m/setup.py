from cx_Freeze import setup, Executable

# exclude unneeded packages
build_exe_options = {"excludes": ["tkinter", "PyQt4.QtSql", "sqlite3", 
                                  "scipy.lib.lapack.flapack",
                                  "PyQt4.QtNetwork",
                                  "PyQt4.QtScript",
                                  "numpy.core._dotblas", 
                                  "PyQt5"],
                     "optimize": 2}

target = Executable("src/klines-5m.py", icon="src/icon.ico")

setup(
  name = "klines-5m" ,
  version = "2.0" ,
  description = "Reads 5m klines from binance public API." ,
  options = {"build_exe": build_exe_options},
  executables = [target]
)