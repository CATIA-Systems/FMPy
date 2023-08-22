@echo off
Rem Local build script. Used for debugging purpose.
echo ***
echo *** Compilation 64bits
echo ***
mkdir build-win64
cd build-win64
cmake .. -A x64 -DRPCLIB=..\..\rpclib-2.3.0\win64\install
cmake --build . --config Release
cd ..
rmdir /s /q  build-win64


echo ***
echo *** Compilation 32bits
echo ***
mkdir build-win32
cd build-win32
cmake .. -A Win32 -DRPCLIB=..\..\rpclib-2.3.0\win32\install
cmake --build . --config Release
cd ..
rmdir /s /q  build-win32

echo ***
echo *** DONE
echo ***