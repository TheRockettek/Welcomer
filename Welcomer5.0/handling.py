import os
import aiohttp

async def exit(self, opcode, args):
    async with aiohttp.ClientSession() as session:
        await session.post(f"http://{self.config['ipc_host']}:{self.config['ipc_port']}/api/pushstatus/{self.cluster_id}/0")
    os._exit(0)

async def hang(self, opcode, args):
    async with aiohttp.ClientSession() as session:
        await session.post(f"http://{self.config['ipc_host']}:{self.config['ipc_port']}/api/pushstatus/{self.cluster_id}/4")
    os._exit(2)

async def restart(self, opcode, args):
    async with aiohttp.ClientSession() as session:
        await session.post(f"http://{self.config['ipc_host']}:{self.config['ipc_port']}/api/pushstatus/{self.cluster_id}/1")
    os._exit(1)

async def details(self, opcode, args):
    responce = {
        "guilds": len(self.guilds),
        "members": len(list(self.get_all_members())),
        "latency": self.latency,
        "latencies": list(l[1] for l in self.latencies),
        "status": ("Ready" if self.is_ready() else "Connecting")
    }
    return responce
