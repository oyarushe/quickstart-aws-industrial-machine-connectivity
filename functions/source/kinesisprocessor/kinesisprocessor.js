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
        
        if (obj.payload.values[0].value.hasOwnProperty('integerValue')) {
            const result = "'"+obj.payload.assetId+"','"+obj.payload.propertyId+"',"+obj.payload.values[0].timestamp.timeInSeconds+","+obj.payload.values[0].value.integerValue+"\n"
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