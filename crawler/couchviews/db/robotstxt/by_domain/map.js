function (doc) {
    if(doc.type == "robotstxt") {
        emit([doc.protocol, doc.domain], doc._id);
    }
}
