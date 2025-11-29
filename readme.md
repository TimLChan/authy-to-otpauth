# authy-to-otpauth

Converts Authy tokens to otpauth:// URIs.

This takes the output json from [AlexTech01/Authy-iOS-MiTM](https://github.com/AlexTech01/Authy-iOS-MiTM) and converts it to an `otpauth://` string with some opinions of how it should be formatted.

This script also aims to fix weird TOTP accounts when Authy does not include the `issuer`, or has a weird `account name` due to the original TOTP import missing these fields.

## features

- Automatically fixes missing issuer fields from the decrypted Authy TOTP
- Automatically updates the account name when the issuer is also present
- Interactive mode to confirm or edit the issuer / account name for tokens that require input

## usage

1. Use [AlexTech01/Authy-iOS-MiTM](https://github.com/AlexTech01/Authy-iOS-MiTM) to decrypt your Authy TOTP tokens.
2. Run `python convert.py` to convert the decrypted tokens to otpauth:// URIs
3. Import into whichever TOTP / 2FA app you want to use

### examples

```bash
usage: convert.py [-h] [-i INPUT] [-o OUTPUT] [--interactive]

Convert decrypted Authy TOTP tokens to the otpauth:// URI format

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Path to the decrypted Authy TOTP JSON file (default: decrypted_tokens.json)
  -o OUTPUT, --output OUTPUT
                        Path to the output file for otpauth:// URIs (default: otpauth_uris.txt)
  --interactive         Enable interactive mode to confirm or edit the issuer / account name for tokens that require input

Examples:
  python convert.py
  python convert.py -i my_tokens.json -o my_uris.txt
  python convert.py --input decrypted_tokens.json --output otpauth_uris.txt
  python convert.py --interactive
```
