@echo off
Rem Local build script. Used for debugging purpose.
echo ***
echo *** Compilation 64bits
echo ***
mkdir build-win64
cd build-win64
cmake .. -A x64
cmake --build . --config Release
cd ..
rmdir /s /q  build-win64


echo ***
echo *** Compilation 32bits
echo ***
mkdir build-win32
cd build-win32
cmake .. -A Win32 
cmake --build . --config Release
cd ..
rmdir /s /q  build-win32

echo ***
echo *** DONE
echo ***