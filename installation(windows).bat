@echo off
python -m venv venv
venv\Scripts\activate.bat
pip install git+https://github.com/dolfies/discord.py-self.git audioop-lts aiohttp webhooks
python MessageCopier.py
