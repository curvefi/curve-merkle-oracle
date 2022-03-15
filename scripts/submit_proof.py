import eth_abi
import rlp
from brownie import StateSender, VotingEscrowStateOracle, accounts, web3
from hexbytes import HexBytes

VOTING_ESCROW = "0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2"
ORACLE = "0x12F407340697Ae0b177546E535b91A5be021fBF9"
BLOCK_NUMBER = 14309414

# https://github.com/ethereum/go-ethereum/blob/master/core/types/block.go#L69
BLOCK_HEADER = (
    "parentHash",
    "sha3Uncles",
    "miner",
    "stateRoot",
    "transactionsRoot",
    "receiptsRoot",
    "logsBloom",
    "difficulty",
    "number",
    "gasLimit",
    "gasUsed",
    "timestamp",
    "extraData",
    "mixHash",
    "nonce",
    "baseFeePerGas",  # added by EIP-1559 and is ignored in legacy headers
)


ACCOUNT = "0xbabe61887f1de2713c6f97e567623453d3C79f67"


def serialize_block(block):
    block_header = [
        HexBytes("0x") if isinstance((v := block[k]), int) and v == 0 else HexBytes(v)
        for k in BLOCK_HEADER
        if k in block
    ]
    return rlp.encode(block_header)


def serialize_proofs(proofs):
    account_proof = list(map(rlp.decode, map(HexBytes, proofs["accountProof"])))
    storage_proofs = [
        list(map(rlp.decode, map(HexBytes, proof["proof"]))) for proof in proofs["storageProof"]
    ]
    return rlp.encode([account_proof, *storage_proofs])


def generate_proof():
    block_header_rlp = serialize_block(web3.eth.get_block(BLOCK_NUMBER))
    if BLOCK_NUMBER > 14310929:
        proof_params = StateSender.at(ORACLE).generate_eth_get_proof_params(
            ACCOUNT, block_identifier=BLOCK_NUMBER
        )
    else:
        proof_params = web3.eth.call(
            {
                "to": ORACLE,
                "data": web3.keccak(text="generate_eth_get_proof_params(address)")[:4].hex()
                + "00" * 12
                + ACCOUNT[2:],
            },
            block_identifier=BLOCK_NUMBER,
            state_override={ORACLE: {"code": StateSender._build["deployedBytecode"]}},
        )
        proof_params = eth_abi.decode_single("(address,uint256[20],uint256)", proof_params)
    proof_rlp = serialize_proofs(web3.eth.get_proof(VOTING_ESCROW, *proof_params[1:]))

    with open(f"block_header_rlp-{BLOCK_NUMBER}.txt", "w") as f:
        f.write(block_header_rlp.hex())

    with open(f"proof_rlp-{BLOCK_NUMBER}-{ACCOUNT}.txt", "w") as f:
        f.write(proof_rlp.hex())


def submit_proof():
    dev = accounts.load("dev")
    oracle = VotingEscrowStateOracle.at(ORACLE)

    with open(f"block_header_rlp-{BLOCK_NUMBER}.txt") as f:
        block_header_rlp = f.read()

    with open(f"proof_rlp-{BLOCK_NUMBER}-{ACCOUNT}.txt") as f:
        proof_rlp = f.read()

    oracle.submit_state(ACCOUNT, block_header_rlp, proof_rlp, {"from": dev})
