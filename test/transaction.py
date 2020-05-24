import base64
import hashlib
import json
from typing import Any, Dict, List

import ecdsa
import requests

from hdacpy.exceptions import BadRequestException, EmptyMsgException, NotEnoughParametersException
from hdacpy.type import SyncMode
from hdacpy.wallet import privkey_to_address, privkey_to_pubkey, pubkey_to_address


class Transaction:
    """A Hdac transaction."""

    def __init__(
        self,
        *,
        host: str,
        privkey: str,
        memo: str = "",
        chain_id: str = "friday-devnet",
        sync_mode: SyncMode = "sync",
    ) -> None:
        self._host = host
        self._privkey = privkey
        self._account_num = 0
        self._sequence = -1 #0
        self._gas_price = 0
        self._memo = memo
        self._chain_id = chain_id
        self._sync_mode = sync_mode
        self._msgs: List[dict] = []

    def _get(self, url: str, params: dict) -> requests.Response:
        resp = requests.get(url, params=params)
        return resp

    def _post_json(self, url: str, json_param: dict) -> requests.Response:
        resp = requests.post(url, json=json_param)
        return resp

    def _put_json(self, url: str, json_param: dict) -> requests.Response:
        resp = requests.put(url, json=json_param)
        return resp

    def _get_account_info(self, address):
        url = "/".join([self._host, "auth/accounts", address])
        res = self._get(url, None)
        if res.status_code != 200:
            raise BadRequestException

        resp = res.json()
        self._account_num = int(resp["result"]["value"]["account_number"])
        self._sequence += 1 #int(resp["result"]["value"]["sequence"])

    def _get_pushable_tx(self) -> str:
        pubkey = privkey_to_pubkey(self._privkey)
        base64_pubkey = base64.b64encode(bytes.fromhex(pubkey)).decode("utf-8")
        pushable_tx = {
            "tx": {
                "msg": self._msgs,
                "fee": {"gas": str(self._gas_price), "amount": [],},
                "memo": self._memo,
                "signatures": [
                    {
                        "signature": self._sign(),
                        "pub_key": {"type": "tendermint/PubKeySecp256k1", "value": base64_pubkey},
                        "account_number": str(self._account_num),
                        "sequence": str(self._sequence),
                    }
                ],
            },
            "mode": self._sync_mode,
        }
        return pushable_tx

    def _sign(self) -> str:
        message_str = json.dumps(self._get_sign_message(), separators=(",", ":"), sort_keys=True)
        message_bytes = message_str.encode("utf-8")

        privkey = ecdsa.SigningKey.from_string(bytes.fromhex(self._privkey), curve=ecdsa.SECP256k1)
        signature_compact = privkey.sign_deterministic(
            message_bytes, hashfunc=hashlib.sha256, sigencode=ecdsa.util.sigencode_string_canonize
        )

        signature_base64_str = base64.b64encode(signature_compact).decode("utf-8")
        return signature_base64_str

    def _get_sign_message(self) -> Dict[str, Any]:
        return {
            "chain_id": self._chain_id,
            "account_number": str(self._account_num),
            "fee": {"gas": str(self._gas_price), "amount": [],},
            "memo": self._memo,
            "sequence": str(self._sequence),
            "msgs": self._msgs,
        }

    def _clear_msgs(self):
        self._msgs = []

    def _send_tx(self):
        tx = self._get_pushable_tx()
        url = "/".join([self._host, "txs"])
        resp = self._post_json(url, json_param=tx)
        print(tx)
        print(resp.text)
        self._clear_msgs()

        if resp.status_code != 200:
            raise BadRequestException
        return resp.json()


    ############################
    ## Transaction
    ############################

    ##############
    ## Query
    ##############

    def get_tx(self, tx_hash: str):
        url = "/".join([self._host, "txs", tx_hash])
        resp = self._get(url, None)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        return resp.json()


    # Looks like silly but possible in python
    def get_blocks(self, height: int = "latest"):
        url = "/".join([self._host, "blocks", height])
        resp = self._get(url, None)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        return resp.json()


    ############################
    ## Contract
    ############################

    ## Tx

    def execute_contract(
        self,
        execution_type: str,
        token_contract_address_or_key_name: str,
        base64_encoded_binary: str,
        args: str,
        gas_price: int,
        fee: int,
        memo: str = "",
    ):
        sender_pubkey = privkey_to_pubkey(self._privkey)
        sender_address = pubkey_to_address(sender_pubkey)

        self._gas_price = gas_price
        self._memo = memo
        self._get_account_info(sender_address)

        if execution_type == "wasm":
            token_contract_address_or_key_name = ""
        else: # hash | uref | name
            base64_encoded_binary = ""

        url = "/".join([self._host, "contract"])
        params = {
            "base_req": {
                "chain_id": self._chain_id,
                "memo": memo,
                "gas": str(gas_price),
                "from": sender_address,
            },
            "type": execution_type,
            "token_contract_address_or_key_name": token_contract_address_or_key_name,
            "base64_encoded_binary": base64_encoded_binary,
            "args": args,
            "fee": str(fee),
        }
        resp = self._post_json(url, json_param=params)
        if resp.status_code != 200:
            raise BadRequestException

        value = resp.json().get("value")
        msgs = value.get("msg")
        if len(msgs) == 0:
            raise EmptyMsgException

        self._msgs.extend(msgs)
        return self._send_tx()


    ## Query

    def query_contract(
        self,
        data_type: str,
        data: str,
        path: str
    ):
        url = "/".join([self._host, "contract"])
        params = {
            "data_type": data_type,
            "data": data,
            "path": path
        }
        resp = self._get(url, params)
        if resp.status_code != 200:
            raise BadRequestException

        return resp.json()


    ############################
    ## Token
    ############################

    ## Tx

    def transfer(
        self,
        recipient_address: str,
        amount: int,
        gas_price: int,
        fee: int,
        memo: str = "",
    ):
        sender_pubkey = privkey_to_pubkey(self._privkey)
        sender_address = pubkey_to_address(sender_pubkey)

        self._gas_price = gas_price
        self._memo = memo
        self._get_account_info(sender_address)

        url = "/".join([self._host, "hdac/transfer"])
        params = {
            "base_req": {
                "chain_id": self._chain_id,
                "memo": memo,
                "gas": str(gas_price),
                "from": sender_address,
            },
            "fee": str(fee),
            "recipient_address_or_nickname": recipient_address,
            "amount": str(amount),
        }
        resp = self._post_json(url, json_param=params)
        if resp.status_code != 200:
            raise BadRequestException

        value = resp.json().get("value")
        msgs = value.get("msg")
        if len(msgs) == 0:
            print(resp.text)
            raise EmptyMsgException

        self._msgs.extend(msgs)
        return self._send_tx()

    def bond(
        self,
        amount: int,
        gas_price: int,
        fee: int,
        memo: str = ""
    ):
        pubkey = privkey_to_pubkey(self._privkey)
        address = pubkey_to_address(pubkey)

        self._gas_price = gas_price
        self._memo = memo
        self._get_account_info(address)

        url = "/".join([self._host, "hdac/bond"])
        params = {
            "base_req": {
                "chain_id": self._chain_id,
                "memo": memo,
                "gas": str(gas_price),
                "from": address,
            },
            "fee": str(fee),
            "amount": str(amount),
        }
        resp = self._post_json(url, json_param=params)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        value = resp.json().get("value")
        msgs = value.get("msg")
        if len(msgs) == 0:
            raise EmptyMsgException

        self._msgs.extend(msgs)
        return self._send_tx()

    def unbond(
        self,
        amount: int,
        gas_price: int,
        fee: int,
        memo: str = ""
    ):
        pubkey = privkey_to_pubkey(self._privkey)
        address = pubkey_to_address(pubkey)

        self._gas_price = gas_price
        self._memo = memo
        self._get_account_info(address)

        url = "/".join([self._host, "hdac/unbond"])
        params = {
            "base_req":{
                "chain_id": self._chain_id,
                "memo": memo,
                "gas": str(gas_price),
                "from": address,
            },
            "fee": str(fee),
            "amount": str(amount),
        }
        resp = self._post_json(url, json_param=params)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        value = resp.json().get("value")
        msgs = value.get("msg")
        if len(msgs) == 0:
            raise EmptyMsgException

        self._msgs.extend(msgs)
        return self._send_tx()

    def delegate(
        self,
        validator_address: str,
        amount: int,
        gas_price: int,
        fee: int,
        memo: str = ""
    ):
        pubkey = privkey_to_pubkey(self._privkey)
        address = pubkey_to_address(pubkey)

        self._gas_price = gas_price
        self._memo = memo
        self._get_account_info(address)

        url = "/".join([self._host, "hdac/delegate"])
        params = {
            "base_req":{
                "chain_id": self._chain_id,
                "memo": memo,
                "gas": str(gas_price),
                "from": address,
            },
            "validator_address": validator_address,
            "amount": str(amount),
            "fee": str(fee),
        }
        resp = self._post_json(url, json_param=params)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        value = resp.json().get("value")
        msgs = value.get("msg")
        if len(msgs) == 0:
            raise EmptyMsgException

        self._msgs.extend(msgs)
        return self._send_tx()

    def undelegate(
        self,
        validator_address: str,
        amount: int,
        gas_price: int,
        fee: int,
        memo: str = ""
    ):
        pubkey = privkey_to_pubkey(self._privkey)
        address = pubkey_to_address(pubkey)

        self._gas_price = gas_price
        self._memo = memo
        self._get_account_info(address)

        url = "/".join([self._host, "hdac/undelegate"])
        params = {
            "base_req":{
                "chain_id": self._chain_id,
                "memo": memo,
                "gas": str(gas_price),
                "from": address,
            },
            "validator_address": validator_address,
            "amount": str(amount),
            "fee": str(fee),
        }
        resp = self._post_json(url, json_param=params)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        value = resp.json().get("value")
        msgs = value.get("msg")
        if len(msgs) == 0:
            raise EmptyMsgException

        self._msgs.extend(msgs)
        return self._send_tx()

    def redelegate(
        self,
        src_validator_address: str,
        dest_validator_address: str,
        amount: int,
        gas_price: int,
        fee: int,
        memo: str = ""
    ):
        pubkey = privkey_to_pubkey(self._privkey)
        address = pubkey_to_address(pubkey)

        self._gas_price = gas_price
        self._memo = memo
        self._get_account_info(address)

        url = "/".join([self._host, "hdac/redelegate"])
        params = {
            "base_req":{
                "chain_id": self._chain_id,
                "memo": memo,
                "gas": str(gas_price),
                "from": address,
            },
            "src_validator_address": src_validator_address,
            "dest_validator_address": dest_validator_address,
            "amount": str(amount),
            "fee": str(fee),
        }
        resp = self._post_json(url, json_param=params)
        if resp.status_code != 200:
            raise BadRequestException

        value = resp.json().get("value")
        msgs = value.get("msg")
        if len(msgs) == 0:
            raise EmptyMsgException

        self._msgs.extend(msgs)
        return self._send_tx()

    def vote(
        self,
        target_contract_address: str,
        amount: int,
        gas_price: int,
        fee: int,
        memo: str = ""
    ):
        pubkey = privkey_to_pubkey(self._privkey)
        address = pubkey_to_address(pubkey)

        self._gas_price = gas_price
        self._memo = memo
        self._get_account_info(address)

        url = "/".join([self._host, "hdac/vote"])
        params = {
            "base_req":{
                "chain_id": self._chain_id,
                "memo": memo,
                "gas": str(gas_price),
                "from": address,
            },
            "target_contract_address": target_contract_address,
            "amount": str(amount),
            "fee": str(fee),
        }
        resp = self._post_json(url, json_param=params)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        value = resp.json().get("value")
        msgs = value.get("msg")
        if len(msgs) == 0:
            raise EmptyMsgException

        self._msgs.extend(msgs)
        return self._send_tx()

    def unvote(
        self,
        target_contract_address: str,
        amount: int,
        gas_price: int,
        fee: int,
        memo: str = ""
    ):
        pubkey = privkey_to_pubkey(self._privkey)
        address = pubkey_to_address(pubkey)

        self._gas_price = gas_price
        self._memo = memo
        self._get_account_info(address)

        url = "/".join([self._host, "hdac/unvote"])
        params = {
            "base_req":{
                "chain_id": self._chain_id,
                "memo": memo,
                "gas": str(gas_price),
                "from": address,
            },
            "target_contract_address": target_contract_address,
            "amount": str(amount),
            "fee": str(fee),
        }
        resp = self._post_json(url, json_param=params)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        value = resp.json().get("value")
        msgs = value.get("msg")
        if len(msgs) == 0:
            raise EmptyMsgException

        self._msgs.extend(msgs)
        return self._send_tx()

    def claim(
        self,
        reward_or_commission: bool,
        gas_price: int,
        fee: int,
        memo: str = ""
    ):
        pubkey = privkey_to_pubkey(self._privkey)
        address = pubkey_to_address(pubkey)

        self._gas_price = gas_price
        self._memo = memo
        self._get_account_info(address)

        url = "/".join([self._host, "hdac/claim"])
        params = {
            "base_req":{
                "chain_id": self._chain_id,
                "memo": memo,
                "gas": str(gas_price),
                "from": address,
            },
            "reward_or_commission": reward_or_commission,
            "fee": str(fee),
        }
        resp = self._post_json(url, json_param=params)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        value = resp.json().get("value")
        msgs = value.get("msg")
        if len(msgs) == 0:
            raise EmptyMsgException

        self._msgs.extend(msgs)
        return self._send_tx()


    ## Query

    def get_balance(self, address: str, blockHash: str = None):
        url = "/".join([self._host, "hdac/balance"])
        params = {"address": address}
        #print(blockHash, type(blockHash))
        #if blockHash != None and blockHash != "":
        #    params["block"] = blockHash

        resp = self._get(url, params=params)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        return resp.json()

    def get_delegator(self, validator_address: str, delegator_address: str):
        if (validator_address == None or validator_address == "") and \
            (delegator_address == None or delegator_address == ""):
            raise NotEnoughParametersException

        params = {}
        if not (validator_address == None or validator_address == ""):
            params['validator'] = validator_address

        if not (delegator_address == None or delegator_address == ""):
            params['delegator'] = delegator_address

        url = "/".join([self._host, "hdac/delegator"])
        resp = self._get(url, params=params)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        return resp.json()

    def get_voter(self,
            account_address: str = None,
            contract_address: str = None
        ):

        if (account_address == None or account_address == "") and \
            (contract_address == None or contract_address == ""):
            raise NotEnoughParametersException

        params = {}
        if not (account_address == None or account_address == ""):
            params['address'] = account_address

        if not (contract_address == None or contract_address == ""):
            params['contract'] = contract_address

        url = "/".join([self._host, "hdac/voter"])
        resp = self._get(url, params=params)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        return resp.json()

    def get_reward(self, account_address: str):
        url = "/".join([self._host, "hdac/reward"])
        resp = self._get(url, params={"address": account_address})
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        return resp.json()

    def get_commission(self, account_address: str):
        url = "/".join([self._host, "hdac/commission"])
        resp = self._get(url, params={"address": account_address})
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        return resp.json()


    ############################
    ## Validator
    ############################

    ## Tx
    def create_validator(
        self,
        validator_address: str,
        cons_pub_key: str,
        moniker: str,
        gas_price: int,
        identity: str = "",
        website: str = "",
        details: str = "",
        memo: str = "",
    ):
        pubkey = privkey_to_pubkey(self._privkey)
        address = pubkey_to_address(pubkey)

        self._gas_price = gas_price
        self._memo = memo
        self._get_account_info(address)

        url = "/".join([self._host, "hdac/validators"])
        params = {
            "base_req":{
                "chain_id": self._chain_id,
                "memo": memo,
                "gas": str(gas_price),
                "from": validator_address,
            },
            "cons_pub_key": cons_pub_key,
            "description": {
                "moniker": moniker,
                "identity": identity,
                "website": website,
                "details": details,
            },
        }
        resp = self._post_json(url, json_param=params)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        value = resp.json().get("value")
        msgs = value.get("msg")
        if len(msgs) == 0:
            raise EmptyMsgException

        self._msgs.extend(msgs)
        return self._send_tx()

    def edit_validator(
        self,
        validator_address: str,
        moniker: str,
        gas_price: int,
        identity: str = "",
        website: str = "",
        details: str = "",
        memo: str = "",
    ):
        pubkey = privkey_to_pubkey(self._privkey)
        address = pubkey_to_address(pubkey)

        self._gas_price = gas_price
        self._memo = memo
        self._get_account_info(address)

        url = "/".join([self._host, "hdac/validators"])
        params = {
            "base_req":{
                "chain_id": self._chain_id,
                "memo": memo,
                "gas": str(gas_price),
                "from": validator_address,
            },
            "description": {
                "moniker": moniker,
                "identity": identity,
                "website": website,
                "details": details,
            },
        }
        resp = self._put_json(url, json_param=params)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        value = resp.json().get("value")
        msgs = value.get("msg")
        if len(msgs) == 0:
            raise EmptyMsgException

        self._msgs.extend(msgs)
        return self._send_tx()


    ## Query

    def get_validators(self, account_address: str):
        url = "/".join([self._host, "hdac/validators"])
        resp = self._get(url, params={"address": account_address})
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        return resp.json()


    ###################################
    ## Nickname
    ##   - Will be blocked for a while
    ###################################

    ## Tx
    def set_nick(self, name: str, gas_price: int, memo: str = ""):
        pubkey = privkey_to_pubkey(self._privkey)
        address = pubkey_to_address(pubkey)

        self._gas_price = gas_price
        self._memo = memo
        self._get_account_info(address)

        url = "/".join([self._host, "nickname/new"])
        params = {
            "base_req": {
                "chain_id": self._chain_id,
                "gas": str(gas_price),
                "memo": memo,
                "from": address,
            },
            "nickname": name,
        }
        resp = self._post_json(url, json_param=params)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        value = resp.json().get("value")
        msgs = value.get("msg")
        if len(msgs) == 0:
            raise EmptyMsgException

        self._msgs.extend(msgs)
        return self._send_tx()

    def changekey(self, name: str, newaddr: str, gas_price: int, memo: str = ""):
        oldpubkey = privkey_to_pubkey(self._privkey)
        oldaddr = pubkey_to_address(oldpubkey)

        self._gas_price = gas_price
        self._memo = memo
        self._get_account_info(oldaddr)

        url = "/".join([self._host, "nickname/change"])
        params = {
            "base_req":{
                "chain_id": self._chain_id,
                "gas": str(gas_price),
                "memo": memo,
                "from": oldaddr,
            },
            "name": name,
            "new_address": newaddr,
        }
        resp = self._put_json(url, json_param=params)
        if resp.status_code != 200:
            print(resp.text)
            raise BadRequestException

        value = resp.json().get("value")
        msgs = value.get("msg")
        if len(msgs) == 0:
            raise EmptyMsgException

        self._msgs.extend(msgs)
        return self._send_tx()
