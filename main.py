import time
import argparse
import pandas as pd
from threading import Thread
from api import discord_interface
from api.db_interface import DBConnector
from api import queries as q

def stake_change_listener(pool_hash, client):
    print("Stake change listener started for", pool_hash)
    prev_stake = pd.DataFrame(db_conn.execute(q.get_live_stake_from_hash.format(pool_hash)))

    while True:
        time.sleep(10*60)
        stake = pd.DataFrame(db_conn.execute(q.get_live_stake_from_hash.format(pool_hash)))

        if not stake.equals(prev_stake):
            _prev_stake = prev_stake.copy()
            _stake = stake.copy()

            lost_df = _stake.merge(_prev_stake, on=['stake_addr'], how='right', indicator=True)
            lost_delegators = lost_df[lost_df['_merge'] == 'right_only'][['stake_id_y', 'stake_addr', 'stake_y']]
            lost_delegators.rename(columns={'stake_id_y': 'stake_id', 'stake_y': 'stake'}, inplace=True)

            new_df = _stake.merge(_prev_stake, on=['stake_addr'], how='left', indicator=True)
            new_delegators = new_df[new_df['_merge'] == 'left_only'][['stake_id_x', 'stake_addr', 'stake_x']]
            new_delegators.rename(columns={'stake_id_x': 'stake_id', 'stake_x': 'stake'}, inplace=True)

            _prev_stake.drop(lost_delegators.index, inplace=True)
            _prev_stake.reset_index(inplace=True, drop=True)
            _stake.drop(new_delegators.index, inplace=True)
            _stake.reset_index(inplace=True, drop=True)

            _stake['stake_change'] = _stake['stake'] - _prev_stake['stake']
            _stake['old_stake'] = _prev_stake['stake']
            stake_change = _stake[_stake['stake_change'] != 0]

            stake_change_msg = ""
            deleg_change_msg = ""
            reward_payout_msg = ""
            if len(lost_delegators) > 0:
                for idx, row in lost_delegators.iterrows():
                    msg = "\N{broken heart} {} (₳{:,.0f}) just left us"\
                        .format(row['stake_addr'][:12], int(row['stake'] / 10**6))
                    deleg_change_msg += msg + '\n'
            if len(new_delegators) > 0:
                for idx, row in new_delegators.iterrows():
                    msg = "\N{Growing heart} {} (₳{:,.0f}) just joined us"\
                        .format(row['stake_addr'][:12], int(row['stake'] / 10**6))
                    deleg_change_msg += msg + '\n'
            if abs(stake_change['stake_change'].sum()) < 50*10**6:
                # Transaction between staked wallets - Ignore
                #print("inerwallet, ingonre", stake_change['stake_change'].max())
                pass
            elif len(stake_change) > len(stake)*0.50:
                # If more than 50% of delegated addr increase stake, probably stake rewards
                msg = "\N{Cut of meat} ₳{:,.0f} in staking rewards has been paid out" \
                    .format(int(stake_change['stake_change'].sum() / 10**6))
                reward_payout_msg += msg + '\n'
            elif len(stake_change) > 0:
                for idx, row in stake_change.iterrows():
                    if abs(row['stake_change']) < 50*10**6:
                        # Ignore stake change less than 50 ADA
                        continue
                    elif row['stake_change'] > 0:
                        msg = "\N{money bag} {} (₳{:,.0f}) just added ₳{:,.0f}"\
                            .format(row['stake_addr'][:12], int(row['old_stake']/10**6), int(row['stake_change'] / 10**6))
                    else:
                        msg = "\N{money with wings} {} (₳{:,.0f}) just removed ₳{:,.0f}"\
                            .format(row['stake_addr'][:12], int(row['old_stake']/10**6), int(-row['stake_change'] / 10**6))
                    stake_change_msg += msg + '\n'

            if len(stake_change_msg) > 0:
                client.send(stake_change_msg, 'stake_change')
            if len(deleg_change_msg) > 0:
                client.send(deleg_change_msg, 'delegator_change')
            if len(reward_payout_msg) > 0:
                client.send(reward_payout_msg, 'staking_rewards')

        prev_stake = stake.copy()

def block_listener(clients, block):
    leader_ids = dict()
    for hash in clients:
        l_id = db_conn.execute(q.get_leader_id_from_hash.format(hash))
        if l_id is None:
            continue
        if len(l_id) > 0:
            l_id = l_id[0]['id']
        else:
            continue
        clients[hash].leader_id = l_id
        leader_ids[l_id] = hash

    while True:
        slot_no = block.get()
        block_info = db_conn.execute(q.get_block_info.format(slot_no))

        if len(block_info) > 0:
            block_info = block_info[0]
        else:
            continue

        block_id = block_info['id']
        txs_info = db_conn.execute(q.get_tx_info.format(block_id))
        if len(txs_info) > 0:
            txs_info = txs_info[0]
        else:
            txs_info = None

        minting_leader = block_info['slot_leader_id']
        if minting_leader in leader_ids.keys():
            client = clients[leader_ids[minting_leader]]
            block_hash = block_info['hash'].hex()

            if txs_info is None:
                resp = "\N{fire}We just minted a block!\N{fire}\nThe block is empty"
                client.send(resp, 'minted_block')
                continue

            n_contracts = db_conn.execute(q.get_n_sc.format(block_id))
            if len(n_contracts) == 0:
                n_contracts = 0
            else:
                n_contracts = n_contracts[0]['n_contracts']

            n_native_tokens = db_conn.execute(q.get_n_tokens.format(block_id))
            if len(n_native_tokens) == 0:
                n_native_tokens = 0
            else:
                n_native_tokens = n_native_tokens[0]['n_tokens']

            resp = "\N{fire}We just minted a block!\N{fire}\n" \
                   "The block consists of {} transactions, containing:\n" \
                   "\N{scroll} {} Smart contract interactions\n" \
                   "\N{Radio button} {} Native tokens\n" \
                   "\N{money bag} ₳{:,.0f}\n" \
                   "\N{money with wings} Costing ₳{:.2f} in fees\n" \
                   "\N{floppy disk} This block is {:.0f}% full\n" \
                   "https://eutxo.org/block/{}".format(txs_info['n_tx'],
                                                       n_contracts,
                                                       n_native_tokens,
                                                       int(txs_info['tot_ada']) / 1000000,
                                                       int(txs_info['tot_fee']) / 1000000,
                                                       int(txs_info['tot_size']) / 90000 * 100,
                                                       block_hash)

            client.send(resp, 'minted_block')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Welcome to TECH-bot')
    parser.add_argument('--dbname', default='cexplorer', help='Database name')
    parser.add_argument('--dbuser', default='postgres', help='Database user name')
    parser.add_argument('--dbpassword', default='dbpassword', help='Database password')
    parser.add_argument('--dbhost', default='localhost', help='Database host name')
    parser.add_argument('--dbport', default=5432, help='Database host name')
    parser.add_argument('--webhooks', default='discord_whs.json', help='Path to json-file with webhook URLs')
    args = parser.parse_args()

    db_conn = DBConnector(args.dbuser, args.dbpassword, args.dbname, args.dbhost, args.dbport)
    clients = discord_interface.get_discord_clients(args.webhooks)

    block_q = db_conn.start_block_listener()
    Thread(target=block_listener, args=(clients, block_q, ), daemon=True).start()

    for hash in clients:
        Thread(target=stake_change_listener, args=(hash, clients[hash]), daemon=True).start()

    while True:
        time.sleep(69)
