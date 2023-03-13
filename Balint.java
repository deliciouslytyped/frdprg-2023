import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;

public class Source_2 {
    public static void main(String[] args)
            throws IOException {
        Path fileName
                = Path.of("res/proba.txt"); /*{ertekadas lesz} a1:=23<>(*nem egyenlo*)a2 $*/

        String forras = Files.readString(fileName);

        for (int i = 0; i < forras.length(); i++) {
            System.out.print(forras.charAt(i) + " ");
        }
        System.out.print("\n");
        int allapot = 1; //kezdo
        int pozicio = 0;

        StringBuilder valtozo_Str = new StringBuilder("");
        StringBuilder output = new StringBuilder("");

        ArrayList<String> vars_str = new ArrayList<>();
        ArrayList<String> comment = new ArrayList<>();

        while (allapot != 21) {
            System.out.println("-------------");
            char jel = forras.charAt(pozicio);
            switch (allapot) {
                case 1: //kezdo
                    System.out.println("1 kezdoallapot");
                    System.out.println("Talált: "+ jel);
                    pozicio = pozicio + 1;
                    valtozo_Str.delete(0, valtozo_Str.length());
                    if (Character.isLetter(jel) && jel!='$') {
                        allapot = 2;
                        valtozo_Str.append(jel);
                        break;
                    } else {
                        if (Character.isDigit(jel)) {
                            allapot = 4;
                            break;
                        }
                    }

                    switch (jel) {
                        case '{':
                            allapot = 6;
                            break;
                        case '}':
                        case '*':
                        case ')':
                        case '=':
                            allapot = 19;
                            break;
                        case '(':
                            allapot = 8;
                            break;
                        case ':':
                            allapot = 12;
                            break;
                        case '<':
                            allapot = 14;
                            break;
                        case '>':
                            allapot = 17;
                            break;
                        case ' ':
                            allapot = 1;
                            break;
                        case '$':
                            allapot = 21;
                            break;
                        default:
                            allapot = 19;
                            break;
                    }
                    break;
                case 2:

                    System.out.println("2. allapot");
                    System.out.println("Talált: "+ jel);
                    pozicio = pozicio + 1;
                    if (Character.isLetterOrDigit(jel)) {
                        valtozo_Str.append(jel);
                    } else {
                        allapot = 3;
                    }
                    break;
                case 3:
                    System.out.println("3. allapot");
                    System.out.println("Nem olvas");
                    allapot = 1;
                    pozicio = pozicio - 1;
                    vars_str.add(valtozo_Str.toString());
                    output.append("<azonosito>");
                    break;
                case 4:
                    System.out.println("4. allapot");
                    System.out.println("Talált: "+ jel);
                    pozicio = pozicio + 1;
                    if (!Character.isDigit(jel)) {
                        allapot = 5;
                    }

                    break;
                case 5:
                    System.out.println("5. allapot");
                    System.out.println("Nem olvas");
                    allapot = 1;
                    pozicio = pozicio - 1;
                    output.append("<konstans>");
                    break;
                case 6:
                    System.out.println("6. allapot");
                    System.out.println("Talált: "+ jel);
                    pozicio = pozicio + 1;
                    if(Character.isAlphabetic(jel) && jel!='}' && jel!='$'){
                        valtozo_Str.append(jel);
                        break;
                    }else {
                        switch (jel) {
                            case '}':
                                allapot = 7;
                                break;
                            case '$':
                                allapot = 19;
                                if (valtozo_Str.length() != 0) {
                                    comment.add(valtozo_Str.substring(0,valtozo_Str.length()));
                                }
                                break;
                        }
                    }
                    break;
                case 7:
                    System.out.println("7. allapot");
                    System.out.println("Nem olvas");
                    allapot = 1;
                    comment.add(valtozo_Str.toString());
                    break;
                case 8:
                    System.out.println("8. allapot");
                    System.out.println("Talált: "+ jel);
                    pozicio=pozicio+1;
                    switch (jel) {
                        case '*':
                            allapot=9;
                            break;
                        case '$':
                            allapot=19;
                            if (valtozo_Str.length()!=0) {
                                comment.add(valtozo_Str.toString());
                            }
                            break;
                        default:
                            allapot=20;
                            break;
                    }
                    break;
                case 9:
                    System.out.println("9. allapot");
                    System.out.println("Talált: "+ jel);
                    pozicio=pozicio+1;
                    if(Character.isAlphabetic(jel) && jel!='*' && jel!='$'){
                        valtozo_Str.append(jel);
                        break;
                    }else {
                        switch (jel) {
                            case '*':
                                allapot = 10;
                                break;
                            case '$':
                                allapot = 19;
                                if (valtozo_Str.length() != 0) {
                                    comment.add(valtozo_Str.toString());
                                }
                                break;
                        }
                    }
                    break;
                case 10:
                    System.out.println("10. allapot");
                    System.out.println("Talált: "+ jel);
                    pozicio=pozicio+1;
                    if(Character.isAlphabetic(jel) && jel!='*' && jel!='$'){
                        valtozo_Str.append(jel);
                        allapot=9;
                        break;
                    }else {
                        switch (jel) {
                            case '*':
                                allapot = 10;
                                break;
                            case '$':
                                allapot = 19;
                                if (valtozo_Str.length() != 0) {
                                    comment.add(valtozo_Str.toString());
                                }
                                break;
                            case ')':
                                allapot = 11;
                                break;
                        }
                    }
                    break;
                case 11:
                    System.out.println("11. allapot");
                    System.out.println("Nem olvas");
                    allapot=1;
                    comment.add(valtozo_Str.toString());
                    break;
                case 12:
                    System.out.println("12. allapot");
                    System.out.println("Talált: "+ jel);
                    pozicio=pozicio+1;
                    switch (jel) {
                        case '=':
                            allapot=13;
                            break;
                        case '$':
                            allapot=19;
                            break;
                        default:
                            allapot=20;
                    }
                    break;
                case 13:
                    System.out.println("13. allapot");
                    System.out.println("Nem olvas");
                    allapot=1;
                    output.append("<:=>");
                    break;
                case 14:
                    System.out.println("14. allapot");
                    System.out.println("Talált: "+ jel);
                    pozicio=pozicio+1;
                    switch (jel) {
                        case '=':
                            allapot=15;
                            break;
                        case '>':
                            allapot=16;
                            break;
                        case '$':
                            allapot=19;
                            break;
                        default:
                            allapot=20;
                    }
                    break;
                case 15:
                    System.out.println("15. allapot");
                    System.out.println("Nem olvas");
                    allapot=1;
                    output.append("<<=>");
                    break;
                case 16:
                    System.out.println("16. allapot");
                    System.out.println("Nem olvas");
                    allapot=1;
                    output.append("<<>>");
                    break;
                case 17:
                    System.out.println("17. allapot");
                    System.out.println("Talált: "+ jel);
                    pozicio=pozicio+1;
                    switch (jel) {
                        case '=':
                            allapot=18;
                            break;
                        case '$':
                            allapot=19;
                            break;
                        default:
                            allapot=20;
                    }
                    break;
                case 18:
                    System.out.println("18. allapot");
                    System.out.println("Nem olvas");
                    allapot=1;
                    output.append("<>=>");
                    break;
                case 19:
                    System.out.println("19. allapot");
                    System.out.println("Nem olvas");
                    allapot=1;
                    break;
                case 20:
                    System.out.println("20. allapot");
                    System.out.println("Nem olvas");
                    pozicio=pozicio-1;
                    allapot=1;
                    break;
            }
        }
        if (allapot==21){
            System.out.println("21 stop");
            System.out.println("Token sorozat: " + output);
            System.out.println("Kommentek: "+comment);
            System.out.println("Használt változó nevek: "+vars_str);
        }
    }

}
