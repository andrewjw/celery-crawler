function (doc) {
    if(doc.type == "page") {
        emit(doc.url, doc._id);
    }
}
