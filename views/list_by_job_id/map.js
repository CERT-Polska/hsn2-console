function (doc) {
    if (doc.type == "file" || doc.type == "url")
        emit(doc.job, {
            "object_id": doc._id.split(':')[1],
            "classification": doc.classification,
            "origin": doc.origin,
            "display": doc.url_original || 'File (' + doc['mime type'] + ')',
            "parent": doc.parent
        });
}
