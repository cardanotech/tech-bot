# TECH-bot
This is the backend code for a discord bot that automatically publishes stake pool
updates to a discord server via a webhook. This bot is meant to increase transparency between SPO
and delegators.

## Examples
All the announcements from the bot will be in real-time, here are some examples of what kind of announcements the bot will make:\
![new_block.png](images%2Fnew_block.png)\
Announcement of new block with block information

![stake_payout.png](images%2Fstake_payout.png)\
Announcement of staking rewards paid out

![joining_delegator.png](images%2Fjoining_delegator.png)\
Announcement of joining delegator

![leading_delegator.png](images%2Fleading_delegator.png)\
Announcement of leaving delegator

![added_stake.png](images%2Fadded_stake.png)\
Announcement of increasing stake

![removed_stake.png](images%2Fremoved_stake.png)\
Announcement of decreasing stake

## Requirements
This bot requires a synced version of [cardano-db-sync](https://github.com/input-output-hk/cardano-db-sync)
running either locally or remotely.


## Usage
In this section, we explain how to deploy and run TECH-bot.

### Installing dependencies
The TECH-bot application is dependent on Python3, the package dependencies can be 
installed with the following command:

```commandline
pip install -r requirements.txt
```

### Setting up the webhooks JSON file
TECH-bot can run announcements about multiple stake pools to multiple discord channels. The
bot sends messages to the discord channels via a [webhook](https://hookdeck.com/webhooks/platforms/how-to-get-started-with-discord-webhooks#discord-webhook-example),
the data are stored in a JSON file format where webhooks are stored in lists to a corresponding message class, there can be 
multiple webhook URLs per message class, to mute one message class the webhooks field can be left empty.

```
{
  "pool_hash1": {
  "stake_change": ["https://discordapp.com/api/webhooks/..."],
  "delegator_change": ["https://discordapp.com/api/webhooks/..."],
  "minted_block": ["https://discordapp.com/api/webhooks/...", "https://discordapp.com/api/webhooks/..."],
  "staking_rewards": ["https://discordapp.com/api/webhooks/..."]
  },
  "pool_hash2": {
  "stake_change": ["https://discordapp.com/api/webhooks/..."],
  "delegator_change": [],
  "minted_block": [],
  "staking_rewards": []
  },
  "pool_hash3": {...}
}
```

### Starting TECH-bot
TECH-bot can be started with the following command:
```commandline
python3 main.py --dbname <cexplorer> --dbuser <postgres> --dbpassword <dbpassword> --dbhost <localhost> --dbport <5432> --webhooks <discord_whs.json>
```

## Support
If you like what you see you would like to support me you can stake to 
TECH Pool (Ticker TECH, Hash: a60950c7a6e3f7a8247b34035d0a98cb0d11f2d04ba5fa9fd17e1065) or 
donate some ada to my ADA Handles address $tech.
