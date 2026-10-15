# Troubleshooting

## Server Issues

**Dashboard shows "No transactions"?**
- Verify MQTT subscriber is running
- Check MQTT broker configuration in `config.yaml`
- Ensure fog nodes are publishing to correct topics
- Verify fog node names match `config.yaml`

**Nodes showing as offline?**
- Nodes must send data to update status
- Check `node_offline_threshold` in `config.yaml`
- Verify fog nodes are actively publishing

**MQTT connection fails?**
- Verify broker host/port in `config.yaml`
- Check MQTT broker is running and accessible
- Test with `mosquitto_sub -h <host> -t "#"`

**Database errors?**
- Delete `fog_monitoring.db` and reinitialize
- Check file permissions
- Verify database path in `config.yaml`

**FTP server issues?**
- Ensure FTP server is running on port 21
- Check firewall allows FTP connections
- Verify `ftp_root/` directory exists

## Client Issues

**FTP download fails?**
- Verify FTP server is running on server side
- Check `FTP_HOST`, `FTP_USER`, `FTP_PASS` in `download_models.py`
- Ensure network connectivity to server
- Check firewall allows FTP (port 21)

**MQTT connection fails?**
- Verify `MQTT_BROKER` IP is correct
- Ensure MQTT broker is running and accessible
- Check firewall allows port 1883
- Test connectivity: `ping <MQTT_BROKER>`

**Email alerts not working?**
- Use Gmail App Password, not regular password
- Verify credentials in `.env` file
- Check SMTP settings (`smtp.gmail.com:587`)
- Test with `python scripts/send_test_email.py`

**Model loading errors?**
- Ensure `download_models.py` was run successfully
- Verify `models/` directory contains `.pkl` files
- Check `MODEL_PATH`, `SCALER_PATH` and `DATA_PATH`
