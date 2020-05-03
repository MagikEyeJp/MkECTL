#include "sw2.h"
#include "ui_sw2.h"

sw2::sw2(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::sw2)
{
    ui->setupUi(this);
}

sw2::~sw2()
{
    delete ui;
}
