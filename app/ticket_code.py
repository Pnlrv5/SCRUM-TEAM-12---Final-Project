def generate_ticket_code(full_name):
    # Use only the first name
    first = full_name.strip().split()[0]
    key = "INFOTC4320"
    code = []

    # Alternate characters
    for i in range(max(len(first), len(key))):
        if i < len(first):
            code.append(first[i])
        if i < len(key):
            code.append(key[i])

    return "".join(code)
