from brownie import (
    DaoGovernor,
    DaoGovToken,
    TimeLock,
    DaoBox,
    Contract,
    config,
    network,
    accounts,
    chain,
)
from web3 import Web3, constants

def deploy_governor():
    account = get_account()
    dgv_token = (
        DaoGovToken.deploy(
            {'from': account},
            publish_source=config["networks"][network.show_active()].get(
                "verify", False
            ),
        )
        if len(DaoGovToken) <= 0
        else DaoGovToken[-1]
    )
    dgv_token.delegate(account, {'from': account})
    print(f"Checkpoints: {dgv_token.numCheckpoints(account)}")
    time_lock = (
        TimeLock.deploy(1,[],[],
            {'from': account},
            publish_source=config["networks"][network.show_active()].get(
                "verify", False
            ),
        )
        if len(TimeLock) <= 0
        else TimeLock[-1]
    )
    governor = DaoGovernor.deploy(
        dgv_token.address,
        time_lock.address,
        4,5,1,
        {'from': account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    proposer_role = time_lock.PROPOSER_ROLE()
    executor_role = time_lock.EXECUTOR_ROLE()
    timelock_admin_role = time_lock.TIMELOCK_ADMIN_ROLE()
    time_lock.grantRole(proposer_role, governor, {'from': account})
    time_lock.grantRole(
        executor_role, constants.ADDRESS_ZERO, {'from': account}
    )
    Txn = time_lock.revokeRole(
        timelock_admin_role, account, {'from': account}
    )
    Txn.wait(1)

def deploy_daobox():
    account = get_account()
    dao_box = DaoBox.deploy({'from': account})
    Txn = dao_box.transferOwnership(TimeLock[-1], {'from': account})
    Txn.wait(1)

def get_account(index=None, id=None):
    if index:
        return accounts[index]
    if network.show_active() in ["hardhat", "development", "ganache"]:
        return accounts[0]
    if id:
        return accounts.load(id)
    return accounts.add(config["wallets"]["from_key"])

def propose(store_value):
    account = get_account()
    args = (store_value,)
    encoded_function = Contract.from_abi("DaoBox", DaoBox[-1], DaoBox.abi).store.encode_input(
        *args
    )
    print(encoded_function)
    propose_Txn = DaoGovernor[-1].propose(
        [DaoBox[-1].address],
        [0],
        [encoded_function],
        "Store 1 in the DaoBox.",
        {'from': account},
    )
    if network.show_active() in ["hardhat", "development", "ganache"]:
        Txn = account.transfer(accounts[0], "0 ether")
        Txn.wait(1)
    propose_Txn.wait(2)  
    print(f"Proposal state {DaoGovernor[-1].state(propose_Txn.return_value)}")
    print(
        f"Proposal snapshot {DaoGovernor[-1].proposalSnapshot(propose_Txn.return_value)}"
    )
    print(
        f"Proposal deadline {DaoGovernor[-1].proposalDeadline(propose_Txn.return_value)}"
    )
    return propose_Txn.return_value


def vote(proposal_id: int, vote: int):
    print(f"voting yes on {proposal_id}")
    account = get_account()
    Txn = DaoGovernor[-1].castVoteWithReason(
        proposal_id, vote, "Voting...", {'from': account}
    )
    Txn.wait(1)
    print(Txn.events["VoteCast"])


def queue_and_execute(store_value):
    account = get_account()
    args = (store_value,)
    encoded_function = Contract.from_abi("DaoBox", DaoBox[-1], DaoBox.abi).store.encode_input(
        *args
    )
    description_hash = Web3.keccak(text="Store 1 in the DaoBox.").hex()
    Txn = DaoGovernor[-1].queue(
        [DaoBox[-1].address],
        [0],
        [encoded_function],
        description_hash,
        {'from': account},
    )
    Txn.wait(1)
    Txn = DaoGovernor[-1].execute(
        [DaoBox[-1].address],
        [0],
        [encoded_function],
        description_hash,
        {'from': account},
    )
    Txn.wait(1)
    print(DaoBox[-1].retrieve())


def move_blocks(amount):
    for block in range(amount):
        get_account().transfer(get_account(), "0 ether")
    print(chain.height)

def main():
    deploy_governor()
    deploy_daobox()
    proposal_id = propose(5)
    print(f"Proposal ID {proposal_id}")
    if network.show_active() in ["hardhat", "development", "ganache"]:
        move_blocks(1)
    vote(proposal_id, 1)
    if network.show_active() in ["hardhat", "development", "ganache"]:
        move_blocks(5)
    print(f" This proposal is currently {DaoGovernor[-1].state(proposal_id)}")
    queue_and_execute(5)