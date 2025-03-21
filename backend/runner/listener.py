from backend.runner.singletons import mongo_conn


def stream_listener():
    i = 0
    max_out = 50
    while i < max_out:
        with mongo_conn.db.simulations.watch() as stream:
            for change in stream:
                print(f'Detected a stream change in the simulations collection: {change}')

        i += 1


if __name__ == '__main__':
    stream_listener()

