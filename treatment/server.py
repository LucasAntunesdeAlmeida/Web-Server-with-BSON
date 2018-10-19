import os, sys, getopt
import socket
import threading
import logging

import request_pb2 as request
import response_pb2 as response
import communication
from pathlib import Path

def setDefaultServer(message):
	'''
	Define os valores default da estrutura do protobuf
	Para evitar que faltem parametros no protobuf na hora de enviar ao cliente

	:param message: estrutura protobuf
	:return: estrutura protobuf com os valores definidos
	'''

	message.status = ""
	message.protoVersion = "1.0"
	message.url = ""
	message.serverInfo = "WebServer with Protobuf v1.0"
	message.encoding = "utf-8"
	message.content = ""
	message.signature = ""

	return message

def getMethod(url):
	'''
	Função que popula o protobuf enviando como conteudo, o arquivo que o cliente quer

	:param url: Url do arquivo desejado (ex: "index.html", "teste.txt")
	:return: Protobuf já pronto para o envio
	'''

	message = response.Response()
	archivePath = str(Path().absolute())
	archivePath += '/contents/'

	if not os.path.exists(archivePath):
		os.makedirs("contents")

	message = setDefaultServer(message)

	if(url in ['/','']):
		archivePath += 'index.html'

	else:
		if url[0] != '/':
			archivePath += "/" + url
		else:
			archivePath += url

	message.url = url

	logging.info(" GET {0}".format(url))

	try:
		archive = open(archivePath, 'r')
		message.content += archive.read()
		logging.info(" GET Sucessful")
		message.status = "OK - 200"
		archive.close()
	except FileNotFoundError:
		message.status = "FAIL - 404"
		logging.info(" Archive not found")

	message.signature = communication.hmacFromResponse(message)

	return message

def postMethod(url, clientId, clientInfo, content):
	'''
	Função que cria arquivos no servidor

	Cria um arquivo com o conteudo recebido do cliente
	Para manter a autoridade dos arquivos, também é criado um arquivo, com mesmo nome,
	porém, concatenado com a identificação e informação do cliente.

	:param url: Url onde o arquivo sera salvo
	:param clientId: Identificação do cliente
	:param clientInfo: Informação sobre o cliente, neste caso o hostname
	:return: Estrutura Protobuf já pronta para o envio
	'''

	message = response.Response()
	archivePath = str(Path().absolute())
	archivePath += '/contents/'

	if not os.path.exists(archivePath):
		os.makedirs("contents")

	message = setDefaultServer(message)

	if url == '/':
		archivePath += 'index.html'

	else:
		if url[0] == '/':
			archivePath += str(''.join(url.split('/')))
		else:
			archivePath += url

	logging.info(" POST {0}".format(url))

	if os.path.exists(archivePath):
		logging.info(" POST in a existent file")
		message.status = "FAIL - 403"
	else:
		archivePathLock = archivePath + "." + clientId + clientInfo
		archive = open(archivePath, 'w')
		archiveLock = open(archivePathLock, 'w')

		archive.write(content)
		logging.info(" POST Sucessful")
		message.status = "OK - 200"

		archive.close()
		archiveLock.close()
	message.url = url
	message.content = content
	message.signature = communication.hmacFromResponse(message)

	return message

def deleteMethod(url, clientId, clientInfo):
	'''
	Função de remoção de arquivos

	Remove arquivos localizados no servidor
	Para segurança dos arquivos, faz o teste antes de remover
	O teste basicamente é uma busca pelo arquivo de lock (url + . + clientId + clientInfo)

	:param url: Url do arquivo que será removido
	:param clientId: Identificação do cliente
	:param clientInfo: Informação do cliente, neste caso é o hostname
	:return: Estrutura protobuf de resposta já pronta para envio
	'''

	message = response.Response()
	archivePath = str(Path().absolute())
	archivePath += '/contents/'

	if not os.path.exists(archivePath):
		os.makedirs("contents")

	message = setDefaultServer(message)
	if url == '/':
		archivePath += 'index.html'

	else:
		if url[0] == '/':
			archivePath += str(''.join(url.split('/')))
		else:
			archivePath += url

	logging.info(" DELETE {0}".format(url))

	if os.path.exists(archivePath):
		archivePathLock = archivePath + "." + clientId + clientInfo

		if os.path.exists(archivePathLock):
				os.remove(archivePath)
				os.remove(archivePathLock)
				logging.info(" DELETE Sucessful".format(url))
				message.status = "OK - 200"
		else:
			logging.info(" DELETE Unsucessful".format(url))
			message.status = "FAIL - 403"

	else:
		logging.info(" DELETE Unsucessful".format(url))
		message.status = "FAIL - 403"

	message.url = url
	message.content = ""
	message.signature = communication.hmacFromResponse(message)

	return message

def unknownMethod():
	'''
	Função que é chamada quando o comando especificado pelo cliente não é conhecido
	Ex: "gets", "trace"
	'''

	logging.info(" Unknown command")
	message = response.Response()
	message = setDefaultServer(message)
	message.status = "FAIL - 401"
	message.signature = communication.hmacFromResponse(message)

	return message
