function(doc) {
  if (doc.type == 'url' || doc.type == 'file')
  emit([doc.job, doc.type], doc.classification);
}
