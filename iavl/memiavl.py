from cprotobuf import Field, ProtoEntity, decode_primitive


def scan_wal(input: bytes):
    offset = 0
    while offset < len(input):
        size, n = decode_primitive(input[offset:], "uint64")
        offset += n
        if offset + size > len(input):
            break

        entry = WALEntry()
        entry.ParseFromString(input[offset : offset + size])
        offset += size
        yield entry


class KVPair(ProtoEntity):
    delete = Field("bool", 1)
    key = Field("bytes", 2)
    value = Field("bytes", 3)


class ChangeSet(ProtoEntity):
    pairs = Field(KVPair, 1, repeated=True)


class NamedChangeSet(ProtoEntity):
    changeset = Field(ChangeSet, 1)
    name = Field("string", 2)


class TreeNameUpgrade(ProtoEntity):
    name = Field("string", 1)
    rename_from = Field("string", 2)
    delete = Field("bool", 3)


class WALEntry(ProtoEntity):
    changeset = Field(NamedChangeSet, 1, repeated=True)
    upgrades = Field(TreeNameUpgrade, 2, repeated=True)


class CommitID(ProtoEntity):
    version = Field("int64", 1)
    hash = Field("bytes", 2)


class StoreInfo(ProtoEntity):
    name = Field("string", 1)
    commit_id = Field(CommitID, 2)


class CommitInfo(ProtoEntity):
    version = Field("int64", 1)
    store_infos = Field(StoreInfo, 2, repeated=True)


class MultiTreeMetadata(ProtoEntity):
    commit_info = Field(CommitInfo, 1)
    initial_version = Field("int64", 2)
