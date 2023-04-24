# Carregamento inteligente de veículos elétricos
O objetivo desse sistema é fonecer um serviço pela internet para orientar de forma automática os motoristas na hora da recarga de seus veículos elétricos, distribuindo a demanda entre os postos de carregamento e reduzindo o tempo necessário para a recarga dos veículos. O carregamento do veículo é requisitado a partir de determinado nível da bateria e deve ser avisado ao motorista onde carregar, levando em consideração a situação atual dos postos de carregamento espalhados pela cidade.

### Autores

[IsraelBraitt](https://github.com/israelbraitt)
[Guilherme Nobre](https://github.com/Helmeppun)

## 2 - Solução do problema

Para desenvolver o sistema foi utilizada a linguagem de programação Python na versão 3.11, bem como funcionalidades incluídas nas bilbiotecas nativas da linguagem, como a utilização de sockets para comunicação em rede e recursos como a biblioteca Eclipse Paho (cliente MQTT) e Eclipse Mosquitto (broker MQTT).

O sistema possui dois modelos de clientes (requisitam os serviços), sendo um que simula a lógica de um carro e o outro a lógica de um posto de carregamento. A arquitetura do sistema é baseada no modelo de névoa, que possui seridores decentralizados (aqui denominado servidores locais), responsáveis por fazer os processamentos iniciais das requisições, que por sua vez estão ligados a um nuvem (aqui denominado servidor central).

A comunicação entre os clientes e os servidores locais são através do protocolo MQTT e dos servidores locais com o servidor central são através do protocolo TCP. Ainda existe a possibilidade do cliente fazer solicitações externas para o software do carro através de uma API REST.

A imagem abaixo representa o diagrama do sistema:

![Diagrama do sistema]()

## 2.1 - O que é MQTT
MQTT (Message Queuing Telemetry Transport) é um protocolo de comunicação máquina para máquina (M2M - Machine to Machine) comumente usado para IoT (Internet of Things), que funciona em cima do protocolo TCP/IP.

O protocolo MQTT funciona de acordo com os princípios do modelo de publicação/assinatura, em que o remetente (publicador) da mensagem é desacoplado do destinatário (assinante) da mensagem. Para isso existe um terceiro componente chamado "agente de mensagens", responsável por filtrar todas as mensagens recebidas dos publicadores e distribuí-las corretamente aos assinantes.

A presença desse terceiro componente permite o desacoplamento em diversos níveis das duas partes citadas anteriormente: publicadores e assinantes não saber a localização um do outro (espacial), não precisam estar conectados ao mesmo tempo (temporal) e eles podem enviar mensagens sem interromper um ao outro (de sincronização).

Para isso ser possível, as mensagens são publicadas em tópicos, que são gerenciados pelos brokers. Os tópicos são organizados de maneira hierárquica, semelhante a um diretório de arquivos ou pastas. Os dispositivos por publicar mensagens nesses tópicos e caso queiram receber mensagens de tópicos específicos, eles devem se inscrever nos mesmos.

Entre os benefícios do protocolo estão:
- Ele é leve e eficiente, sendo que as mensagens transmitidas por ele podem ter apenas poucos bytes de dados, podendo ser usado inclusive em microcontroladores;
- Ele é escalável, sendo que requer poucas linhas de código para funcionar e também é capaz de oferecer suporte à comunicação com um grande número de dispositivos IoT;
- Ele é confiável e seguro, sendo que é possível proteger dados sigilosos e implementar identidade, autenticação e autorização entre clientes e o agente usando diversos certificados ou senhas.

## 2.2 - Carro
O software do carro (ver [car.py]) é responsável por controlar a bateria do mesmo, simulando o descarregamento de acordo com a autonomia do carro e se comunicar com o servidor local de determinada região fazendo a solicitação de um posto de carregamento próximo para recarregar a bateria.

Possui um cliente MQTT e se associa ao servidor local de uma determinada região (geralmente de um bairro), trocando de conexão com outros servidores caso mude de localidade.

Além disso ele possui uma API REST para efetuar comunicação com o usuário do carro, possuindo as seguintes rotas HTTP:
- `/nivel-bateria`
    usada para solicitar o nível da bateria do carro
    
- `/modo`
    usada para solicitar o modo de autonomia atual do carro
    
- `/enviar-localizacao`
    usada para transmitir para o software a localização atual do carro
    
- `/alterar-modo-carro`
    usada para alterar o modo de autonomia do carro

## 2.3 - Posto de carregamento
O software do posto de carregamento (ver [power_station.py]) é responsável por controlar a quantidade de vagas disponíveis e enviá-las para o servidor local. Possui um cliente MQTT e fica associado ao servidor local de uma determinada região (geralmente um determinado bairro), no qual envia as vagas disponíveis.

## 2.4 - Servidores locais
Os servidores locais (ver [local_server.py]) servem para intermediar a comunicação entre os postos de carregamento e os carros, também sendo responsáveis por calcular qual o melhor posto para a solicitação de um carro.

O intuito de implementar eles é diminuir a carga de trabalho do servidor central e distribuir o throughput do sistema como um todo. Com a possibilidade de os servidores locais atenderem boa parte das requisições dos carros à procura de um posto de carregamento, o servidor local fica menos sobrecarregado e recebem requisições apenas quando todos os posto de uma determinada localidade não possuem mais vagas.

Eles possuem um broker para intermediar as mensagens dos carros e dos postos de carregamento, escolhendo qual o melhor posto para cada carro de acordo com o critério do posto que possui mais vagas disponíveis dentre os que enviaram informações nos seus tópicos.

Os tópicos presentes nos brokers dos servidores locais são os seguintes:
- `"REDESP2IG/car/battery"`
    tópico para indicar a bateria baixa dos carros
    
- `"REDESP2IG/station/queue"`
    tópico para atualização das filas dos postos
    
- `"REDESP2IG/station/register"`
    tópico de registro da estação no servidor local
    
- `"REDESP2IG/car/path"`
    tópico para indicar a localização dos carros

## 2.5 - Servidor central
O servidor central (ver [central_server.py]) é responsável por calcular qual o melhor posto para um carro, quando os postos de carregamento de um determinada região não possuem mais vagas disponíveis, com isso o servidor local daquela região encaminha para ele informações do carro (localização e tempo restante da bateria).

## 3. Observações gerais
Para utilizar esse sistema para comunicação com outras máquinas é recomendado que seja alterado o endereço de HOST dos servidors, sendo substituído pelo IP do computador que está executando o servidor. Caso seja necessário, altere também as portas de comunicação, para evitar quaisquer conflitos com portas que já estão sendo utilizadas por outras aplicações.

## Referências
[MQTT - Getting Started](https://mqtt.org/getting-started/) - Tutoriais iniciais para o MQTT

[O que é MQTT? - Amazon AWS](https://aws.amazon.com/pt/what-is/mqtt/) - Conceitos sobre MQTT

[Eclipse Mosquito](https://mosquitto.org/) - Broker MQTT open source

[Eclipse Paho MQTT Python client library](https://pypi.org/project/paho-mqtt) - Biblioteca Python que fornece funcionalidade para clientes MQTT

[//]: # (Referências do relatório)
   [car.py]: <https://github.com/israelbraitt/carregamento-inteligente-de-veiculos-eletricos/blob/main/client%20car/car.py>
   [power_station.py]: <https://github.com/israelbraitt/carregamento-inteligente-de-veiculos-eletricos/blob/main/client%20power%20station/power_station.py>
   [local_server.py]: <https://github.com/israelbraitt/carregamento-inteligente-de-veiculos-eletricos/blob/main/local%20server/local_server.py>
   [central_server.py]: <https://github.com/israelbraitt/carregamento-inteligente-de-veiculos-eletricos/blob/main/central%20server/central_server.py>
   
   
