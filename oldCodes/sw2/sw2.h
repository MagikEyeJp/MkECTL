#ifndef SW2_H
#define SW2_H

#include <QWidget>

namespace Ui {
class sw2;
}

class sw2 : public QWidget
{
    Q_OBJECT

public:
    explicit sw2(QWidget *parent = nullptr);
    ~sw2();

private:
    Ui::sw2 *ui;
};

#endif // SW2_H
