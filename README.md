# discord-account-generator

I run a few Discord bots and got tired of burning my personal accounts when testing rate-limit edge cases. This tool registers throwaway accounts in bulk using a pool of emails and rotating proxies.

## install

pip install -r requirements.txt

## usage

The tool skips already-used emails and writes valid tokens as newline-delimited JSON. Expect some failures; Discord's registration flow changes often and this is best-effort.

<!-- updated: 2026-10-07 -->
