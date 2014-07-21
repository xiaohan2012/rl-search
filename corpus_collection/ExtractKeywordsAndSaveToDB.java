import KPminer.Extractor;

import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Connection;

import java.util.ArrayList;
import org.json.simple.JSONArray;

import java.io.StringWriter;
import java.io.IOException;

public class ExtractKeywordsAndSaveToDB
{
    
    public static void main(String[] args) throws SQLException, ClassNotFoundException
    {
	
	
	Extractor extractor = new Extractor();
	extractor.refinePhrases(true);
	extractor.setCutOff(800);

	PreparedStatement prepSelStmt = null;
	PreparedStatement prepUpdStmt = null;
	ResultSet rs = null;	
	Connection conn = null;
	
	Class.forName("com.mysql.jdbc.Driver");

	conn = DriverManager
	    .getConnection("jdbc:mysql://ugluk/scinet3?"
			   + "user=hxiao&password=xh24206688");

	// prepSelStmt = conn.prepareStatement("SELECT id, abstract FROM archive WHERE id = ?");
	prepSelStmt = conn.prepareStatement("SELECT id, processed_content as abstract FROM webpage WHERE id = ?");
	// prepUpdStmt = conn.prepareStatement("UPDATE archive SET keywords = ? WHERE id = ?");
	
	//Integer upper = 69853;
	Integer upper = 163;
	for(Integer rowId = upper; rowId <= upper; rowId++){
	    System.out.println(rowId);

	    prepSelStmt.setInt(1, rowId);
	
	    rs = prepSelStmt.executeQuery();
	
	    rs.next();

	    String abst = rs.getString("abstract");

	    String [] topKeys = extractor.getTopN(12, abst, false);
	
	    JSONArray list = new JSONArray();
	
	    for(int i=0; i < topKeys.length; i++){
		list.add(topKeys[i]);
	    }
	
	    try{
		StringWriter out = new StringWriter();
		list.writeJSONString(out);
		String jsonText = out.toString();
		
		System.out.print(abst);
		System.out.print(jsonText);
		
		// prepUpdStmt.setString(1, jsonText);
		// prepUpdStmt.setInt(2, rowId);
		
		// prepUpdStmt.executeUpdate();

		//conn.commit();				
	    }
	    catch(IOException e){
		e.printStackTrace();
	    }


	}
	
    }
}
