console.log('Loading function');

exports.handler = async (event, context) => {
    let success = 0; // Number of valid entries found
    let failure = 0; // Number of invalid entries found

    /* Process the list of records and transform them */
    const output = event.records.map((record) => {
        // Kinesis data is base64 encoded so decode here
        console.log(record.recordId);
        const payload = (Buffer.from(record.data, 'base64')).toString('ascii');
        console.log('Decoded payload:', payload);
        var obj = JSON.parse(payload);
        if (obj.hasOwnProperty('metrics')) {
            var result = "\n"
            obj.metrics.forEach(element => { 
                console.log(element);
                if (element.value.hasOwnProperty('reference')) {
                    result = result+"'"+element.name+"','"+element.value.reference+"','"+element.value.metrics[0].name+"','"+element.value.metrics[0].timestamp+"','"+element.value.metrics[0].dataType+"','"+element.value.metrics[0].value+"'\n"
                }
            });
            success++;
            console.log("Priting result")
            console.log(result)
            return {
                recordId: record.recordId,
                result: 'Ok',
                data: (Buffer.from(result)).toString('base64'),
            };
        } else {
            failure++;
            return {
                recordId: record.recordId,
                result: 'ProcessingFailed',
                data: record.data,
            };            
        }
    });
    console.log(`Processing completed.  Successful records ${success}, Failed records ${failure}.`);
    return { records: output };
};