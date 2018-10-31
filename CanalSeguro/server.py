#!/usr/bin/env python
# -*- coding: utf-8 -*-

import getopt
import logging
import os
import socket
import sys
import threading
from pathlib import Path

import communication
from treatment.scrypt import key_exchange
from treatment.server import (clearRules, deleteMethod, getMethod, postMethod,
				synFlood, unknownMethod)

try:
   	import bson
except:
	print("Falha ao importar as bibliotecas\nTente: sudo pip3 install bson")

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(threadName)s:%(message)s')

def connected(client, addr, servidor):
	'''
	Função que recebe a conexão

	Trata o protobuf recebido com base nos valores dele (ex: "GET /")

	:param client: Socket de conexão do cliente
	:param addr: Endereço IP e Porta do cliente
	'''

	keyClient=43501#key_exchange(client)
	KeyServidor=43501#key_exchange(servidor)

	while True:
		message = communication.recvMessage(client)
		if message:
			message['signature'] = signature = communication.hmacFromRequest(message, keyClient)
			communication.sendMessage(servidor, message)
			logging.info("[Cliente]Mensagem enviada para o servidor")

			responseFromServer = communication.recvMessage(servidor)
			if responseFromServer:
				communication.sendMessage(client, responseFromServer)
				logging.info("[Servidor]Mensagem enviada para o cliente")

	client.close()

def listenConnection(IpServidor, PortServidor, IpSeguro, PortSeguro):
	'''
	Coloca o servidor para rodar, de fato

	Após, fica escutando a porta e quando chegar alguma conexão, cria um thread para o cliente
	e trata envia para a função que irá tratar a requisição

	:param Ip: Endereço Ip que o servidor irá rodar
	:param Port: Porta em que o servidor irá rodar
	'''

	try:
		bson.patch_socket()
		cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		try:
			cliente.bind((IpSeguro, int(PortSeguro)))
			cliente.listen(10)
		except:
			logging.info("[Seguro]Error on start server")

		try:
			servidor.connect((IpServidor, int(PortServidor)))
			print("[Servidor] Conexão Estabelecida")
		except ConnectionRefusedError:
			print("[Servidor] Conexão Recusada")
			exit(1)

		logging.info("[Servidor] WebServer running on port {0}".format(PortServidor))
		logging.info("[Seguro] WebServer running on port {0}".format(PortSeguro))

		threads = []

		try:
			while True:
				connC, addrC = cliente.accept()
				logging.info(" [Cliente] New Connection from " + str(addrC[0]) + " with port " + str(addrC[1]))

				aux = threading.Thread(target=connected, args=(connC,addrC,servidor))
				aux.setDaemon(True)
				aux.start()
				threads.append(aux)
		except:
			if(os.getuid() == 0):
				clearRules()
			logging.info(" Ending the server execution")

		servidor.close()
		cliente.close()

	except (KeyboardInterrupt, SystemExit):
		if(os.getuid() == 0):
			clearRules()
		logging.info(" Finishing execution of WebServer...")
		pass


def help():
	'''
	Exibe a ajuda

	No servidor, por padrão o parametro "-i/--ip" equivale ao localhost (127.0.0.1)
	'''

	print("WebServer with Protobuf - Server\n")
	print("Métodos disponíveis:\n-> GET - Faz o pedido de um arquivo a um servidor")
	print("-> POST - Envia um arquivo para o servidor")
	print("-> DELETE - Exclui um arquivo do servidor, apenas o dono do arquivo consegue deletar este arquivo")
	print("Uso => python3 {0} -h -i/--ip <IP_Server> -p/--port <Port_Server> -a/--atac <IP_Seguro> -d/--portA <Port_Seguro>".format(sys.argv[0]))
	print("\n\nParametros\n-h\t\tExibe a ajuda")
	print("-i/--ip\t\tParametro que define o IP do servidor")
	print("-p/--port\tParametro que define a Porta em o que o servidor está rodando")
	print("-a/--atac\tParametro que define o IP do Seguro")
	print("-d/--portA\tParametro que define a Porta em que o Seguro esta rodando")

def main(argv):
	'''
	Função principal que define os parametros do programa e também faz a chamada
	da função que colocará o servidor para funcionar

	:param argv: lista de parametros
	'''
	IpServidor = '127.0.0.1'
	IpSeguro = '127.0.0.1'
	PortServidor = 0
	PortSeguro = 0


	try:
		opts, args = getopt.getopt(argv, "hi:p:a:d:",["ip=","port=","atac=","portA"])
	except getopt.GetoptError:
		help()
		sys.exit(1)

	for opt, arg in opts:
		if opt == "-h":
			help()
			sys.exit()
		elif opt in ("-i", "--ip"):
			IpServidor = arg
		elif opt in ("-p", "--port"):
			PortServidor = arg
		elif opt in ("-d", "--portA"):
			PortSeguro = arg
		elif opt in ("-a", "--atac"):
			IpSeguro = arg

	if PortServidor == 0 or PortSeguro == 0:
		help()
		sys.exit(1)

	if(sys.platform == 'linux'):
		if(os.getuid() == 0):
			synFlood()
		else:
			logging.info(" To prevent Syn Flood Attack, run the server with sudo")

	listenConnection(IpServidor, PortServidor, IpSeguro, PortSeguro)

if __name__ == '__main__':
	'''
	Inicio do programa, apenas faz a chamada da função principal
	'''

	main(sys.argv[1:])
