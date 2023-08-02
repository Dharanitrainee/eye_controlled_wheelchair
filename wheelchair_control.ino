 char data;
#define m1 4
#define m2 5
#define m3 6
#define m4 7
#define en1 8
#define en2 9
void setup(){
  Serial.begin(9600);
  pinMode(m1,OUTPUT);
  pinMode(m2,OUTPUT);
  pinMode(m3,OUTPUT);
  pinMode(m4,OUTPUT);
  pinMode(en1, OUTPUT);
  pinMode(en2, OUTPUT);
}
void loop(){
  digitalWrite(en1,HIGH);
  digitalWrite(en2,HIGH);
  if(Serial.available()>0){
    data = Serial.read();
    if(data == '5'){
      digitalWrite(13,HIGH);
      carforward();
      Serial.print("forward");
      Serial.println();
    }
    else if(data == '3')
    {
      carleft();
      Serial.print("left");
      Serial.println();
    }
    else if(data == '4')
    {
      carright();
      Serial.print("right");
      Serial.println();
    }
    else if(data == '6')
    {
      carstop();
      Serial.print("stop");
      Serial.println();
    }
  }
}
void carforward()
{
  digitalWrite(m1,HIGH);
  digitalWrite(m2,LOW);
  digitalWrite(m3,HIGH);
  digitalWrite(m4,LOW);
 }
void carleft()
{
  digitalWrite(m1,HIGH);
  digitalWrite(m2,LOW);
  digitalWrite(m3,LOW);
  digitalWrite(m4,HIGH);
}
void carright()
{
  digitalWrite(m1,LOW);
  digitalWrite(m2,HIGH);
  digitalWrite(m3,HIGH);
  digitalWrite(m4,LOW);
}
void carstop()
{
  digitalWrite(m1,LOW);
  digitalWrite(m2,LOW);
  digitalWrite(m3,LOW);
  digitalWrite(m4,LOW);
}
