from db import alchemy_db as db
# CREATE TABLE openai_logs (
#     id BIGINT AUTO_INCREMENT PRIMARY KEY,
#     user_id BIGINT,
#     timestamp DATETIME,
#     model VARCHAR(50),
#     input_prompt LONGTEXT,
#     output_texts LONGTEXT,
#     functionality VARCHAR(50)
# );

class OpenaiLogs(db.Model):
    __tablename__ = 'openai_logs'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger)
    timestamp = db.Column(db.DateTime)
    model = db.Column(db.String(50))
    input_prompt = db.Column(db.Text)
    output_texts = db.Column(db.Text)
    functionality = db.Column(db.String(50))

    def __init__(self, user_id, timestamp, model, input_prompt, output_texts, functionality):
        self.user_id = user_id
        self.timestamp = timestamp
        self.model = model
        self.input_prompt = input_prompt
        self.output_texts = output_texts
        self.functionality = functionality

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'timestamp': self.timestamp,
            'model': self.model,
            'inputPrompt': self.input_prompt,
            'outputTexts': self.output_texts,
            'functionality': self.functionality
        }