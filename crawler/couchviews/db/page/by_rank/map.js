function (doc) {
    if(doc.type == "page") {
        emit(-doc.rank, doc._id);
    }
}
