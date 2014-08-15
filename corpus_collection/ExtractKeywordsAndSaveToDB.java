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

    private Extractor extractor = null;
    private Connection conn = null;
    
    public ExtractKeywordsAndSaveToDB() throws SQLException, ClassNotFoundException{
	extractor = new Extractor();
	extractor.refinePhrases(true);
	extractor.setCutOff(800);

	Class.forName("com.mysql.jdbc.Driver");

	conn = DriverManager
	    .getConnection("jdbc:mysql://ugluk/scinet3?"
			   + "user=hxiao&password=xh24206688");
    }
    
    public void extractBatch(int from_id, int to_id) throws SQLException{
	for(int i=from_id; i<to_id;i++){
	    extractAndSave(i);
	}
    }
    public void extractAndSave(int rowId) throws SQLException{
	PreparedStatement prepSelStmt = null;
	PreparedStatement prepUpdStmt = null;
	ResultSet rs = null;	

	prepSelStmt = conn.prepareStatement("SELECT id, processed_content as abstract FROM webpage WHERE !isnull(processed_content) and id = ?");
	
	//Integer upper = 69853;
	System.out.println(rowId);

	prepSelStmt.setInt(1, rowId);
	
	rs = prepSelStmt.executeQuery();
	
	if(rs != null && rs.next()){
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
		
		System.out.println(rowId);
	    }
	    catch(IOException e){
		e.printStackTrace();
	    }

	}
	
    }
    public static void main(String[] args) throws SQLException, ClassNotFoundException {	       
	ExtractKeywordsAndSaveToDB e = new ExtractKeywordsAndSaveToDB();
	e.extractBatch(1,250);
    }
}
