# Nombre del ejecutable
TARGET = hello

# Regla por defecto: compilar
all:
	gcc hello.c -o $(TARGET)

# Regla de instalación (la que usará checkinstall)
install:
	install -m 0755 $(TARGET) /usr/local/bin/

# Regla para limpiar archivos temporales
clean:
	rm -f $(TARGET)
