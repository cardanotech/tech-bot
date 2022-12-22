import time
import discord
from discord import Webhook, RequestsWebhookAdapter
import json

class PoolBot:
    def __init__(self, pool_hash, urls: dict):
        self.pool_hash = pool_hash
        self.urls = urls
        self.whs = dict()
        self.update_whs(urls)
        self.leader_log = None
        self.leader_id = None

    def set_leader_log(self, leader_log):
        self.leader_log = leader_log

    def update_whs(self, urls):
        channels = list(urls.keys())
        for channel in channels:
            webhooks = []
            for url in urls[channel]:
                try:
                    webhooks.append(Webhook.from_url(url, adapter=RequestsWebhookAdapter()))
                except discord.InvalidArgument:
                    print(self.pool_hash, channel, url, "Invalid WH URL, skipping")
            self.whs[channel] = webhooks

    def send(self, message, channel, file_path=None):
        for wh in self.whs[channel]:
            if file_path is None:
                wh.send(content=message)
            else:
                wh.send(content=message, file=discord.File(file_path))


def update_whs(client_urls : dict):
    pool_hashes = list(client_urls.keys())

    for pool_hash in pool_hashes:
        pool_whs = dict()
        channels = list(client_urls[pool_hash].keys())
        for channel in channels:
            whs = []
            urls = client_urls[pool_hash][channel]
            for url in urls:
                try:
                    whs.append(Webhook.from_url(url, adapter=RequestsWebhookAdapter()))
                except discord.InvalidArgument:
                    print(pool_hash, channel, url, "Invalid WH URL, skipping")
            pool_whs[channels] = whs

def get_discord_clients(path):
    with open(path, 'rb') as f:
        discord_whs = json.load(f)
    dc_clients = dict()
    pool_hashes = list(discord_whs.keys())
    for pool_hash in pool_hashes:
        dc_clients[pool_hash] = PoolBot(pool_hash, discord_whs[pool_hash])
    return dc_clients


if __name__ == "__main__":
    clients = get_discord_clients('../discord_whs.json')
