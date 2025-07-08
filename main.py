import sys

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "help"

    if command == "backup":
        ...
    elif command == "status":
        ...
    elif command == "notify":
        ...
    else:
        print("Gebruik: watchdog [backup|status|notify|all]")
