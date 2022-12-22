
create_notify = \
"""
CREATE FUNCTION on_insert_to_block() RETURNS trigger AS
$$
BEGIN

    execute E'NOTIFY NEW_BLOCK, \'' || NEW.slot_no || E'\'';

    RETURN NEW;
END
$$
LANGUAGE 'plpgsql' VOLATILE;
"""

create_trigger = \
"""
create trigger trig_on_insert
after insert on BLOCK
for each row
execute procedure on_insert_to_block();
"""

get_leader_id_from_hash = \
"SELECT id FROM slot_leader WHERE hash='\\x{}';"

get_live_stake_from_hash = \
"""
WITH stake AS 
(SELECT d1.addr_id 
FROM delegation d1, pool_hash 
WHERE pool_hash.id=d1.pool_hash_id 
AND pool_hash.hash_raw='\\x{}' 
AND NOT EXISTS 
(SELECT TRUE 
FROM delegation d2 
WHERE d2.addr_id=d1.addr_id 
AND d2.tx_id>d1.tx_id) 
AND NOT EXISTS 
(SELECT TRUE 
FROM stake_deregistration 
WHERE stake_deregistration.addr_id=d1.addr_id 
AND stake_deregistration.tx_id>d1.tx_id)) 

, delegator_list AS
(SELECT stake_id, SUM(total) AS stake 
FROM 
(SELECT stake.addr_id AS stake_id, SUM(value) AS total 
FROM utxo_view 
INNER JOIN stake ON utxo_view.stake_address_id=stake.addr_id 
GROUP BY stake.addr_id 
UNION 
SELECT stake.addr_id, SUM(amount) 
FROM reward 
INNER JOIN stake ON reward.addr_id=stake.addr_id 
WHERE reward.spendable_epoch <= (SELECT MAX(epoch_no) FROM block) 
GROUP BY stake.addr_id 
UNION 
SELECT stake.addr_id, -sum(amount) 
FROM withdrawal 
INNER JOIN stake ON withdrawal.addr_id=stake.addr_id 
GROUP BY stake.addr_id 
) AS t 
GROUP BY stake_id) 

SELECT stake_id, stake_address.view AS stake_addr, stake
FROM delegator_list
INNER JOIN stake_address on stake_id = stake_address.id;
"""

get_block_info = \
"SELECT * FROM block WHERE slot_no = {};"

get_tx_info = \
"""
SELECT COUNT(id) AS n_tx, SUM(fee) AS tot_fee, SUM(out_sum) AS tot_ada, SUM(size) AS tot_size 
FROM tx 
WHERE block_id = {} 
GROUP BY block_id;
"""

get_n_sc = \
"""
SELECT COUNT(id) AS n_contracts
FROM tx
WHERE block_id = {} AND script_size > 0
GROUP BY block_id;
"""

get_n_tokens = \
"""
SELECT COUNT(id) AS n_tokens 
FROM ma_tx_out 
WHERE tx_out_id IN (SELECT id 
FROM tx_out 
WHERE tx_id IN (SELECT id 
FROM tx 
WHERE block_id = {}));
"""
