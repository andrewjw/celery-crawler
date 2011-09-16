function (doc) {
    if(doc.type == "page") {
        for(i = 0; i < doc.links.length; i++) {
            emit(doc.links[i], [doc.rank, doc.links.length]);
        }
    }
}
