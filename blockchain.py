import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4


from flask import Flask, jsonify, request

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        #Создание блока генезиса
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        '''
        Создание нового блока в блокчейне

        :param proof: <int> Доказательства проведенной работы
        :param previous_hash: (Опционально) хеш предыдущего блока
        :return <dict> Новый блок
        '''
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        #перезагрузка текущего списка транзакций
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        '''
        Направляет новую транзакцию в следующий блок

        :param sender: <str> Адрес отправителя
        :param recipient: <str> Адрес получателя
        :param amount: <int> Сумма
        :return: <int> Индекс блока, который будет хранить эту транзакцию.
        '''
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1
        

    @staticmethod
    def hash(block):
        '''
        Создает хэш SHA-256 блока

        :param block: <dict> Блок
        :return: <str>
        '''
        #Мы долны убедиться, что словарь упорядочен, иначе у нас будут непоследовательные хэши
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    @property
    def last_block(self):
        #возвращает последний блок в цепочке
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        '''
        Простая проверка алгоритма:
        -Поиска числа р", так как hash(pp) содержит 4 заглавных нуля, где р - предыдущий
        - р является предыдущим доказательством ,а p" - новым

        :param last_proof: <int>
        :return: <int>
        '''

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        '''
        Подтверждение док-ва: Содержит ли hash(last_proof, proof) 4 заглавных нуля?

        :param last_proof: <int> Предыдущее док-во
        :param proof: <int> Текущее док-во
        :return: <bool> True, если правильно, False, если нет
        '''

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

#создаем экземпляр узла
app = Flask(__name__)

#Генерируем уникальный на глобальном уровне адрес для этого узла
node_identifier = str(uuid4()).replace('-', '')

#Создаем экземпляр блокчейна
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    #Запускаем алгоритм подтверждения работы, чтобы получить следующее подтверждение
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    #Мы должны получить вознаграждение за найденное подтверждение
    #Отправитель "0" означает, что узел заработал крипто-монету
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    #Создаем новый блок, путем внесения его в цепь
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': 'New Block Forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    #Убедиться в том, что необходимые поля находятся среди POST-данных
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    #Создание новой транзакции
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)