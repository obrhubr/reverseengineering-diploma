from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
import re

def decrypt(public_numbers, encrypted_data):
	# Convert encrypted data to an integer
	encrypted_int = int.from_bytes(encrypted_data, byteorder='big')

	# Perform raw RSA operation: c^e % n
	decrypted_int = pow(encrypted_int, public_numbers.e, public_numbers.n)

	# Convert decrypted integer back to bytes
	decrypted_data = decrypted_int.to_bytes(256, byteorder='big')

	return decrypted_data

def remove_padding(decrypted_bytes):
	# Convert the data to a bytearray for easier manipulation
    data = bytearray(decrypted_bytes)
    
    # Check for the start sequence
    start_seq = b'\x00\x01'
    end_seq = b'\x00'
    
    if not data.startswith(start_seq):
        raise ValueError("Data does not start with the expected padding start sequence")
    
    # Remove the start sequence
    data = data[len(start_seq):]
    
    # Find the end sequence in the remaining data
    end_pos = data.find(end_seq)
    if end_pos == -1:
        raise ValueError("Data does not contain the expected padding end sequence")
    
    # Remove the padding up to and including the end sequence
    data = data[end_pos + len(end_seq):]
    
    return bytes(data)
            
def load_diploma(key_der, qr_code):
	# remove first two chars from qr_code (these are a version id)
	# convert qr code to binary
	qr_code = base64.b64decode(qr_code[2:])

	# load the key from pem file
	public_key = serialization.load_pem_public_key(
		b"-----BEGIN RSA PUBLIC KEY-----\n" + key_der + b"\n-----END RSA PUBLIC KEY-----",
		backend=default_backend()
	)

	# Get the public numbers (modulus and exponent)
	pk = public_key.public_numbers()

	decrypted = decrypt(pk, qr_code)
	decrypt_nopadding = remove_padding(decrypted)
	output = decrypt_nopadding.decode("latin1")

	return parse_grades(output)

def parse_grades(data):
	exp = r"(.*)\|(.*)\|(.*)\|([0-9]{2}[0-9]{2}[0-9]{2})\|(.*)\|(.*)\|(.*)\|(.*)"
	matches = re.findall(exp, data)[0]

	grades = {}
	for g in matches[7].split("#"):
		parsed = g.split("~")
		grades[parsed[0]] = parsed[1]
	
	return {
        "exam": matches[0],
        "name": matches[2] + " " + matches[1],
        "birthdate": matches[3],
        "gpa": matches[4],
        "decision": matches[5],
        "grades": grades
	}

if __name__ == "__main__":
	key_der = b"XXXX"
	qr_code = "02...XXX...=="

	diploma = load_diploma(key_der, qr_code)

	print(diploma)