![cuwo](http://mp2.dk/cuwo/logo.png)
[![Build Status](https://travis-ci.org/matpow2/cuwo.svg?branch=master)](https://travis-ci.org/matpow2/cuwo) [![Build status](https://ci.appveyor.com/api/projects/status/t1ik17xyn26b8rx7?svg=true)](https://ci.appveyor.com/project/matpow2/cuwo)
====

cuwo es una implementación de servidor de código abierto para Cube World, escrita en Python y
C++. Actualmente cuenta con la mejor cobertura de protocolos entre todos los proyectos de servidor
y ofrece características como:

* Compatibilidad multiplataforma (Linux, Windows, Mac OS X, FreeBSD, etc.)
* NPCs y mobs, como en un servidor normal
* Registro de archivos/consola
* Mensaje del día (MOTD)
* Scripting (ver el ejemplo mínimo welcome.py)
* Configuración avanzada
* Sistema de baneos
* Comandos (/kick, /say, /whereis, /setclock, /kill, /stun, etc.)
* Gestión de permisos (/login password)
* Bot de IRC
* Script para PvP
* Prevención de ataques DDoS
* Menores requisitos de CPU que un servidor normal
* Optimizaciones en C++
* Servidor maestro en http://cuwo.org
* Soporte para más de 40 jugadores
* ... ¡y mucho más!

Tenga en cuenta que cuwo solo es compatible con arquitecturas x86 y x86-64, por lo que no funcionará en ARM.

Ejecución
=======

Windows
-------

Consulte la
[guía de inicio rápido](https://github.com/matpow2/cuwo/wiki/Quickstart) para
comenzar rápidamente.

Alternativamente, también puede
[compilar desde el código fuente](https://github.com/matpow2/cuwo/wiki/WindowsSource).

Código fuente
------

Asegúrese de tener Python >= 3.6, compiladores nativos y las siguientes
dependencias instaladas:

* `cython`
* `pyrr`

Si desea compatibilidad con bots de IRC, también necesitará el paquete `irc3`.

Estos paquetes se pueden instalar con `pip install cython pyrr irc3`

Para compilar cuwo, ejecute `python setup.py build_ext --inplace`.

Para ejecutar el servidor, ejecute `python -m cuwo.server`.

Para obtener más información, consulte
[Esta guía](https://github.com/matpow2/cuwo/wiki/BuildSource).

Estado
======

En cuanto al protocolo y las funciones, se ha implementado lo siguiente:
* Entrada/salida de jugadores
* Movimiento y animaciones de los jugadores
* Transmisión de magia/flechas, etc.
* Impactos de los jugadores en entidades/otros jugadores
* Recogida/soltado de objetos
* Gestión del tiempo
* Generador de terreno
* Objetos interactivos (puertas, camas)
* Soporte preliminar para criaturas y PNJ

Aún queda mucho por implementar en cuanto a la jugabilidad. Lo más importante es que los PNJ y las criaturas
se han implementado recientemente, así que es posible que surjan algunos problemas relacionados con ellos.

Otras características incluyen:
* Proxy MITM (para ingeniería inversa)
* Convertidor de modelos Cube World/Qubicle (tools/convertqmo.py)
* Visor de mapas (tools/mapviewer.py)