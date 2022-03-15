from brownie import StateSender, VotingEscrowStateOracle, accounts

ANYCALL = "0x37414a8662bc1d25be3ee51fb27c2686e2490a89"

deployer = accounts.load("veOracle-deployer")


def deploy_state_sender():
    if deployer.balance() == 0:
        dev = accounts.load("dev")
        dev.transfer(deployer, 0.08 * 10 ** 18, priority_fee="2 gwei")
    StateSender.deploy({"from": deployer, "priority_fee": "2 gwei"})


def deploy_oracle():
    VotingEscrowStateOracle.deploy(ANYCALL, {"from": deployer})
