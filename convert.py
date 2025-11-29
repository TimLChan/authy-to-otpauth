#!/usr/bin/env python3
"""
Convert decrypted TOTP tokens to otpauth:// URI format.
"""
import json
import urllib.parse
import re
import logging
import argparse

logger = logging.getLogger(__name__)
logging.addLevelName(logging.WARNING, 'WARN')
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)5s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


def strip_issuer_from_name(name, issuer):
    """
    Strip the issuer from the name if it's present (case-insensitive).
    Handles formats like "issuer: account" or "issuer - account" etc.

    Args:
        name: The account name that may contain the issuer
        issuer: The issuer name to strip

    Returns:
        Cleaned account name with whitespace trimmed
    """
    if not name or not issuer:
        return name.strip() if name else ""

    # Create a case-insensitive pattern to match the issuer at the start
    # followed by common separators like ":", "-", or whitespace
    pattern = re.compile(
        r'^' + re.escape(issuer) + r'\s*[:\-\s]\s*',
        re.IGNORECASE
    )

    # Remove the issuer prefix if found
    cleaned_name = pattern.sub('', name)

    return cleaned_name.strip()


def generate_otpauth_uri(token):
    """
    Generate an otpauth:// URI from a token.

    Format: otpauth://totp/ISSUER:ACCOUNT?secret=SECRET&issuer=ISSUER&digits=DIGITS

    Args:
        token: Dictionary containing token information

    Returns:
        otpauth:// URI string
    """
    # Extract token details
    issuer = token.get('issuer', '')
    name = token.get('name', '')
    secret = token.get('decrypted_seed', '')
    digits = token.get('digits', 6)

    # Strip issuer from name if present
    account = strip_issuer_from_name(name, issuer)

    # If account is empty after stripping, use the original name
    if not account:
        account = name.strip()

    # URL encode the issuer and account for the label
    label = f"{issuer}:{account}" if issuer else account
    encoded_label = urllib.parse.quote(label, safe='')

    # Build the URI
    uri = f"otpauth://totp/{encoded_label}"

    # Build query parameters
    params = []
    if secret:
        params.append(f"secret={secret}")
    if issuer:
        # URL encode issuer for query parameter
        encoded_issuer = urllib.parse.quote(issuer, safe='')
        params.append(f"issuer={encoded_issuer}")
    if digits:
        params.append(f"digits={digits}")

    # Add default algorithm (TOTP standard)
    params.append("algorithm=SHA1")

    if params:
        uri += "?" + "&".join(params)

    return uri


def convert_tokens(input_file, output_file, interactive=False):
    """
    Convert all tokens from the JSON file to the otpauth:// URIs.

    Args:
        input_file: Path to the input JSON file
        output_file: Path to the output text file
        interactive: Boolean, if True, ask user to confirm/edit issuer
    """
    try:
        # Read the JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract tokens
        tokens = data.get('decrypted_authenticator_tokens', [])

        if not tokens:
            logger.error("No tokens found in the input file.")
            return

        # Convert each token to otpauth URI
        uris = []
        for token in tokens:
            # Determine issuer
            issuer = token.get('issuer')
            
            if not issuer:
                # 1. Check logo
                logo = token.get('logo')
                if logo and not logo.startswith('authenticator_'):
                    issuer = logo
            
            if not issuer:
                # 2. Check account_type
                account_type = token.get('account_type')
                if account_type and not account_type.startswith('authenticator'):
                    issuer = account_type

            if not issuer:
                # 3. Parse from name
                name = token.get('name', '')
                if ':' in name:
                    issuer = name.split(':')[0].strip()
            
            if not issuer:
                # 4. Fallback to name
                issuer = token.get('name', '').strip()

            if issuer:
                words = issuer.split()
                for i in range(len(words)):
                    if words[i][0].islower():
                        words[i] = words[i][0].upper() + words[i][1:]
                issuer = ' '.join(words)

            # Interactive mode
            if interactive:
                logger.info("")
                logger.warning(f"the account '{token.get('name')}' does not have an issuer")
                logger.info(f"proposed issuer: {issuer}")
                user_input = input("press Enter to accept proposed issuer, or type a new one: ").strip()
                if user_input:
                    issuer = user_input
            
            # Update token with the determined issuer so generate_otpauth_uri uses it
            token['issuer'] = issuer

            # Print to console for verification
            final_issuer = token.get('issuer', 'Unknown')
            account = strip_issuer_from_name(token.get('name', ''), final_issuer)
            if ": " in account and interactive:
                logger.warning(f"the account '{token.get('name')}' may contain the issuer")
                custom_accout_input = input("press Enter to leave the account name untouched, or type a new one: ").strip()
                if custom_accout_input:
                    account = custom_accout_input
                    token['name'] = account

            logger.info(f"processed totp - issuer: {final_issuer} | account: {account}")

            uri = generate_otpauth_uri(token)
            uris.append(uri)

        # Write URIs to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(uris))

        logger.info("")
        logger.info(f"converted {len(uris)} token(s)")
        logger.info(f"URIs written to: {output_file}")

    except FileNotFoundError:
        logger.error(f"error: could not find '{input_file}'")
    except json.JSONDecodeError as e:
        logger.error(f"error: invalid JSON in '{input_file}': {e}")
    except Exception as e:
        logger.error(f"error: {e}")


def main():
    """Main function to handle command line arguments and run conversion."""
    parser = argparse.ArgumentParser(
        description='Convert decrypted Authy TOTP tokens to the otpauth:// URI format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python convert.py
  python convert.py -i my_tokens.json -o my_uris.txt
  python convert.py --input decrypted_tokens.json --output otpauth_uris.txt
  python convert.py --interactive
        '''
    )

    parser.add_argument(
        '-i', '--input',
        default='decrypted_tokens.json',
        help='Path to the decrypted Authy TOTP JSON file (default: decrypted_tokens.json)'
    )

    parser.add_argument(
        '-o', '--output',
        default='otpauth_uris.txt',
        help='Path to the output file for otpauth:// URIs (default: otpauth_uris.txt)'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Enable interactive mode to confirm or edit the issuer / account name for tokens that require input'
    )

    args = parser.parse_args()

    logger.info("running authy to otpauth:// conversion")
    logger.info("")
    convert_tokens(args.input, args.output, args.interactive)


if __name__ == '__main__':
    main()
