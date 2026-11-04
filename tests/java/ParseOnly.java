import com.sun.source.util.JavacTask;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import javax.tools.*;

/** فحص صيغة فقط (بدون Android SDK): يطبع الأخطاء ويخرج بـ 1 إن وُجدت. */
public class ParseOnly {
    public static void main(String[] args) throws Exception {
        JavaCompiler c = ToolProvider.getSystemJavaCompiler();
        DiagnosticCollector<JavaFileObject> d = new DiagnosticCollector<>();
        StandardJavaFileManager fm = c.getStandardFileManager(d, null, null);
        List<File> files = new ArrayList<>();
        for (String a : args) files.add(new File(a));
        JavacTask t = (JavacTask) c.getTask(null, fm, d, null, null, fm.getJavaFileObjectsFromFiles(files));
        t.parse();
        long errors = d.getDiagnostics().stream().filter(x -> x.getKind() == Diagnostic.Kind.ERROR).count();
        d.getDiagnostics().forEach(x -> System.out.println(x.getSource().getName() + ":" + x.getLineNumber() + " " + x.getMessage(null)));
        System.exit(errors == 0 ? 0 : 1);
    }
}
